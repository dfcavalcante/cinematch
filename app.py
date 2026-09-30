"""CineMatch: servidor local que expõe o mesmo recomendador user-kNN avaliado em evaluate.py."""
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
import sqlite3
import threading
import numpy as np
from recommender import ROOT, GENRES, Recommender, load_data

DB = ROOT / 'cinematch.sqlite3'
# Perfis do site recebem IDs 1001, 1002... e não colidem com os 943 usuários do MovieLens.
SITE_OFFSET = 1000

movies, base_ratings, audit = load_data()
ML_USERS = {int(user) for user in base_ratings[:, 0]}


def database():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    con.execute('CREATE TABLE IF NOT EXISTS profiles (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, genres TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP)')
    con.execute('CREATE TABLE IF NOT EXISTS user_ratings (user_id INTEGER NOT NULL, movie_id INTEGER NOT NULL, rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5), created_at TEXT DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY(user_id, movie_id))')
    con.execute('CREATE TABLE IF NOT EXISTS feedback (id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL, usefulness INTEGER NOT NULL CHECK(usefulness BETWEEN 1 AND 5), would_watch INTEGER NOT NULL CHECK(would_watch IN (0, 1)), comment TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP)')
    return con


def build_model():
    """MovieLens + avaliações feitas no site; uma nota do site substitui a do MovieLens para o mesmo par."""
    with database() as con:
        rows = con.execute('SELECT user_id, movie_id, rating FROM user_ratings').fetchall()
    if not rows:
        return Recommender(movies, base_ratings)
    extra = np.array([(row['user_id'], row['movie_id'], row['rating'], 0) for row in rows], dtype=np.int64)
    overridden = set(zip(extra[:, 0].tolist(), extra[:, 1].tolist()))
    keep = np.array([pair not in overridden for pair in zip(base_ratings[:, 0].tolist(), base_ratings[:, 1].tolist())])
    return Recommender(movies, np.vstack([base_ratings[keep], extra]))


model_lock = threading.Lock()
model = build_model()


def refresh_model():
    global model
    with model_lock:
        model = build_model()


def get_profile(user_id):
    if user_id in ML_USERS:
        return {'id': user_id, 'name': f'Usuário MovieLens {user_id}', 'genres': [], 'source': 'movielens'}
    if user_id > SITE_OFFSET:
        with database() as con:
            row = con.execute('SELECT id, name, genres FROM profiles WHERE id = ?', (user_id - SITE_OFFSET,)).fetchone()
        if row:
            return {'id': user_id, 'name': row['name'], 'genres': json.loads(row['genres']), 'source': 'site'}
    raise ValueError('Perfil não encontrado.')


def profile_history(user_id):
    current = model
    if user_id not in current.user_index:
        return []
    row = current.matrix[current.user_index[user_id]]
    history = [dict(movies[int(current.items[i])], rating=int(row[i])) for i in np.flatnonzero(row)]
    return sorted(history, key=lambda movie: (-movie['rating'], movie['title']))


def recommendations(user_id, n=10):
    favorites = set(get_profile(user_id)['genres'])
    current = model
    recs, mode = current.recommend(user_id, n=n)
    if mode == 'fallback' and favorites:
        # Início frio: mantém a ordem da média bayesiana, mas traz primeiro os gêneros declarados.
        recs, _ = current.recommend(user_id, n=len(current.items))
        recs = sorted(recs, key=lambda movie: not favorites.intersection(movie['genres']))[:n]
    method = ('votos dos 40 vizinhos mais parecidos (filtragem colaborativa user-kNN)' if mode == 'collaborative'
              else 'média bayesiana da comunidade' + (' nos seus gêneros favoritos' if favorites else '') + ' (início frio)')
    return [dict(movie, genre_match=bool(favorites.intersection(movie['genres']))) for movie in recs], mode, method


def profiles():
    with database() as con:
        rows = con.execute('SELECT id, name, genres FROM profiles ORDER BY id DESC').fetchall()
    return [{'id': SITE_OFFSET + row['id'], 'name': row['name'], 'genres': json.loads(row['genres'])} for row in rows]


def valid_rating(movie, rating):
    movie, rating = int(movie), int(rating)
    if movie not in movies or rating not in range(1, 6):
        raise ValueError('Filme ou nota inválida.')
    return movie, rating


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT / 'web'), **kwargs)

    def json(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        self.send_response(status); self.send_header('Content-Type', 'application/json; charset=utf-8'); self.send_header('Content-Length', len(body)); self.end_headers(); self.wfile.write(body)

    def read_body(self):
        return json.loads(self.rfile.read(int(self.headers.get('Content-Length', 0))) or b'{}')

    def do_GET(self):
        url, query = urlparse(self.path), parse_qs(urlparse(self.path).query)
        try:
            if url.path == '/api/summary':
                current = model
                return self.json({'movies': len(movies), 'ratings': int(current.mask.sum()), 'users': len(current.users),
                                  'movielens_users': len(ML_USERS), 'site_profiles': len(profiles())})
            if url.path == '/api/genres': return self.json([genre for genre in GENRES if genre != 'Desconhecido'])
            if url.path == '/api/profiles': return self.json(profiles())
            if url.path == '/api/movies':
                term, current = query.get('q', [''])[0].casefold(), model
                found = [movie for movie in movies.values() if term in movie['title'].casefold()]
                popularity = lambda movie: -int(current.item_counts[current.item_index[movie['id']]])
                return self.json(sorted(found, key=lambda movie: (popularity(movie), movie['title']))[:12])
            if url.path == '/api/profile':
                user_id = int(query['id'][0]); return self.json({**get_profile(user_id), 'history': profile_history(user_id)})
            if url.path == '/api/recommendations':
                recs, mode, method = recommendations(int(query['profile'][0])); return self.json({'recommendations': recs, 'mode': mode, 'method': method})
        except (ValueError, KeyError, IndexError) as error:
            return self.json({'error': str(error)}, 400)
        return super().do_GET()

    def do_POST(self):
        try:
            body = self.read_body()
            if self.path == '/api/profiles':
                name, genres = str(body.get('name', '')).strip()[:60], sorted(set(body.get('genres', [])))
                if not name: raise ValueError('Informe seu nome.')
                if not genres or not set(genres).issubset(GENRES): raise ValueError('Selecione pelo menos um gênero válido.')
                values = dict(valid_rating(row['movie'], row['rating']) for row in body.get('ratings', []))
                with database() as con:
                    user_id = SITE_OFFSET + con.execute('INSERT INTO profiles(name, genres) VALUES (?, ?)', (name, json.dumps(genres))).lastrowid
                    con.executemany('INSERT INTO user_ratings(user_id, movie_id, rating) VALUES (?, ?, ?)', [(user_id, movie, rating) for movie, rating in values.items()])
                if values: refresh_model()
                return self.json({'id': user_id}, 201)
            if self.path == '/api/rating':
                user_id = int(body['profile']); get_profile(user_id)
                movie, rating = valid_rating(body['movie'], body['rating'])
                with database() as con: con.execute('INSERT OR REPLACE INTO user_ratings(user_id, movie_id, rating) VALUES (?, ?, ?)', (user_id, movie, rating))
                refresh_model()
                return self.json({'ok': True})
            if self.path == '/api/feedback':
                user_id = int(body['profile']); get_profile(user_id)
                usefulness, would_watch = int(body['usefulness']), body.get('would_watch')
                if usefulness not in range(1, 6): raise ValueError('A utilidade deve ser de 1 a 5.')
                if would_watch not in (True, False): raise ValueError('Responda se assistiria a pelo menos um filme.')
                with database() as con:
                    con.execute('INSERT INTO feedback(user_id, usefulness, would_watch, comment) VALUES (?, ?, ?, ?)',
                                (user_id, usefulness, int(would_watch), str(body.get('comment', '')).strip()[:500]))
                return self.json({'ok': True}, 201)
        except (ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
            return self.json({'error': str(error)}, 400)
        self.json({'error': 'Rota inexistente'}, 404)


if __name__ == '__main__':
    print('CineMatch em http://localhost:8000')
    ThreadingHTTPServer(('127.0.0.1', 8000), Handler).serve_forever()
