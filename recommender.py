"""Filtragem colaborativa user-kNN; somente NumPy e biblioteca padrão."""
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent
GENRES = ['Desconhecido', 'Ação', 'Aventura', 'Animação', 'Infantil', 'Comédia',
          'Crime', 'Documentário', 'Drama', 'Fantasia', 'Noir', 'Terror',
          'Musical', 'Mistério', 'Romance', 'Ficção científica', 'Suspense', 'Guerra', 'Faroeste']


def load_data(directory=None):
    directory = Path(directory or ROOT / 'data' / 'ml-100k')
    if not (directory / 'u.data').exists():
        raise FileNotFoundError('Execute python download_data.py antes de iniciar.')
    movies = {}
    for line in (directory / 'u.item').read_text(encoding='latin-1').splitlines():
        fields = line.split('|')
        movies[int(fields[0])] = {'id': int(fields[0]), 'title': fields[1],
                                 'genres': [g for g, flag in zip(GENRES, fields[5:]) if flag == '1']}
    raw = np.loadtxt(directory / 'u.data', dtype=np.int64, ndmin=2)
    valid = (raw[:, 0] > 0) & np.isin(raw[:, 1], list(movies)) & (raw[:, 2] >= 1) & (raw[:, 2] <= 5) & (raw[:, 3] > 0)
    clean = raw[valid]
    # Havendo pares repetidos, a interação mais recente prevalece.
    pairs = {}
    for row in clean[np.argsort(clean[:, 3], kind='stable')]:
        pairs[int(row[0]), int(row[1])] = row
    ratings = np.asarray(list(pairs.values()), dtype=np.int64)
    return movies, ratings, {'raw': len(raw), 'invalid': int((~valid).sum()),
                             'duplicates': len(clean) - len(ratings), 'clean': len(ratings)}


class Recommender:
    def __init__(self, movies, ratings, k=40, shrinkage=10.0, prior=20.0):
        self.movies, self.k, self.shrinkage = movies, k, shrinkage
        self.users = sorted(set(int(u) for u in ratings[:, 0]))
        self.user_index = {u: i for i, u in enumerate(self.users)}
        self.items = np.array(sorted(movies), dtype=int)
        self.item_index = {int(m): i for i, m in enumerate(self.items)}
        self.matrix = np.zeros((len(self.users), len(self.items)), dtype=np.float64)
        for u, m, r, *_ in ratings:
            self.matrix[self.user_index[int(u)], self.item_index[int(m)]] = r
        self.mask = self.matrix > 0
        counts = self.mask.sum(axis=1)
        self.means = self.matrix.sum(axis=1) / np.maximum(counts, 1)
        self.centered = np.where(self.mask, self.matrix - self.means[:, None], 0)
        self.norms = np.linalg.norm(self.centered, axis=1)
        self.item_counts = self.mask.sum(axis=0)
        self.global_mean = float(self.matrix.sum() / max(self.mask.sum(), 1))
        self.baseline = (self.matrix.sum(axis=0) + prior * self.global_mean) / (self.item_counts + prior)

    def profile(self, user, overrides=None):
        row = self.matrix[self.user_index[user]].copy() if user in self.user_index else np.zeros(len(self.items))
        for movie, rating in (overrides or {}).items():
            if movie not in self.item_index or not 1 <= rating <= 5:
                raise ValueError('Filme ou nota inválida.')
            row[self.item_index[movie]] = rating
        return row

    def scores(self, user, overrides=None):
        """Nota prevista de cada filme, suporte (vizinhos que o avaliaram) e modo."""
        return self._neighborhood(user, overrides)[:3]

    def _neighborhood(self, user, overrides=None):
        row = self.profile(user, overrides)
        known = row > 0
        empty = np.zeros(len(self.items))
        if known.sum() < 2:
            return self.baseline.copy(), np.zeros(len(self.items), dtype=int), 'fallback', empty
        mean = row[known].mean()
        centered = np.where(known, row - mean, 0)
        norm = np.linalg.norm(centered)
        if norm == 0:
            return self.baseline.copy(), np.zeros(len(self.items), dtype=int), 'fallback', empty
        denominator = self.norms * norm
        sim = np.divide(self.centered @ centered, denominator, out=np.zeros(len(self.users)), where=denominator > 0)
        common = self.mask @ known.astype(float)
        sim *= common / (common + self.shrinkage)
        sim[common < 2] = 0
        if user in self.user_index:
            sim[self.user_index[user]] = 0
        neighbors = np.argsort(-sim, kind='stable')[:self.k]
        neighbors = neighbors[sim[neighbors] > 0]
        if not len(neighbors):
            return self.baseline.copy(), np.zeros(len(self.items), dtype=int), 'fallback', empty
        weights = sim[neighbors]
        totals = weights @ self.mask[neighbors]
        residual = weights @ self.centered[neighbors]
        estimates = np.divide(residual, totals, out=np.zeros(len(self.items)), where=totals > 0) + mean
        scores = np.where(totals > 0, np.clip(estimates, 1, 5), self.baseline)
        # Votos: soma dos desvios ponderados pela similaridade. Diferente da média, cresce com o número
        # de vizinhos que gostaram do filme, então um único vizinho não coloca um título raro no topo.
        return scores, self.mask[neighbors].sum(axis=0), 'collaborative', residual

    def recommend(self, user, n=10, overrides=None, baseline=None):
        """baseline=None usa o user-kNN; 'bayes' ordena pela média bayesiana; 'popular', pelo nº de avaliações."""
        if baseline == 'bayes':
            scores, support, mode, votes = self.baseline.copy(), np.zeros(len(self.items), dtype=int), 'fallback', np.zeros(len(self.items))
        elif baseline == 'popular':
            scores, support, mode, votes = self.item_counts.astype(float), np.zeros(len(self.items), dtype=int), 'fallback', np.zeros(len(self.items))
        else:
            scores, support, mode, votes = self._neighborhood(user, overrides)
        row = self.profile(user, overrides)
        candidates = np.flatnonzero((row == 0) & (self.item_counts > 0))
        # Ordena pelos votos dos vizinhos; empates (inclusive o início frio, sem votos) seguem a nota prevista.
        order = candidates[np.lexsort((self.items[candidates], -scores[candidates], -votes[candidates]))][:n]
        return [dict(self.movies[int(self.items[i])], score=round(float(scores[i]), 4),
                     support=int(support[i]), count=int(self.item_counts[i]),
                     method='collaborative' if support[i] > 0 else 'fallback') for i in order], mode
