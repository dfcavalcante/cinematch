"""Avaliação reprodutível, sem usar notas de teste no ajuste do modelo."""
import json
import platform
from pathlib import Path
import hashlib
import numpy as np
from recommender import ROOT, Recommender, load_data


def split_data(ratings, seed=42):
    rng = np.random.default_rng(seed)
    train, test = [], []
    for user in sorted(set(ratings[:, 0])):
        rows = ratings[ratings[:, 0] == user]
        order = rng.permutation(len(rows))
        n_test = max(1, int(len(rows) * .2))
        test.extend(rows[order[:n_test]])
        train.extend(rows[order[n_test:]])
    return np.asarray(train), np.asarray(test)


def ranking_metrics(recommended, relevant, k=10):
    hits = [int(i in relevant) for i in recommended[:k]]
    dcg = sum(hit / np.log2(rank + 2) for rank, hit in enumerate(hits))
    ideal = sum(1 / np.log2(rank + 2) for rank in range(min(k, len(relevant))))
    return {'precision@10': sum(hits) / k, 'recall@10': sum(hits) / len(relevant) if relevant else 0,
            'ndcg@10': dcg / ideal if ideal else 0}


def main():
    movies, ratings, audit = load_data()
    train, test = split_data(ratings)
    model = Recommender(movies, train)
    results = {}
    examples = []
    per_user = []
    for baseline, label in ((None, 'user_knn'), ('bayes', 'media_bayesiana'), ('popular', 'mais_populares')):
        errors, rank_metrics, covered = [], [], set()
        for user in model.users:
            heldout = test[test[:, 0] == user]
            if baseline != 'popular':  # popularidade só ordena, não prevê nota
                scores = model.baseline if baseline == 'bayes' else model.scores(user)[0]
                errors.extend(float(scores[model.item_index[int(m)]] - r) for _, m, r, _ in heldout)
            recs, _ = model.recommend(user, baseline=baseline)
            ids = [r['id'] for r in recs]
            covered.update(ids)
            relevant = {int(m) for _, m, r, _ in heldout if r >= 4}
            metrics = ranking_metrics(ids, relevant)
            if relevant:
                rank_metrics.append(metrics)
            per_user.append({'model': label, 'user': user, 'relevant': len(relevant), **metrics})
            if baseline is None and user in (1, 2, 3, 4, 5):
                known = train[train[:, 0] == user]
                examples.append({'user': user, 'train_size': len(known), 'test_size': len(heldout),
                                 'relevant_test': len(relevant), 'metrics': metrics,
                                 'history_sample': [{'title': movies[int(m)]['title'], 'rating': int(r)} for _, m, r, _ in known[:5]],
                                 'recommendations': [dict(r, hit=r['id'] in relevant) for r in recs]})
        errors = np.array(errors)
        results[label] = {'mae': float(np.abs(errors).mean()) if len(errors) else None,
                          'rmse': float(np.sqrt(np.mean(errors ** 2))) if len(errors) else None,
                          **{key: float(np.mean([m[key] for m in rank_metrics])) for key in rank_metrics[0]},
                          'catalog_coverage@10': len(covered) / int((model.item_counts > 0).sum()),
                          'ranking_users': len(rank_metrics)}
    output = ROOT / 'results'
    output.mkdir(exist_ok=True)
    payload = {'seed': 42, 'split': '80/20 aleatório por usuário (piso no tamanho de teste)',
               'train': len(train), 'test': len(test), 'users': len(model.users), 'items': len(movies),
               'audit': audit, 'parameters': {'k': 40, 'shrinkage': 10, 'prior': 20, 'relevance': 4, 'ranking': 'soma ponderada dos desvios dos vizinhos (votos)'},
               'environment': {'python': platform.python_version(), 'numpy': np.__version__},
               'data_sha256': hashlib.sha256((ROOT / 'data/ml-100k/u.data').read_bytes()).hexdigest(),
               'metrics': results, 'examples': examples, 'cold_start': model.recommend(944)[0]}
    (output / 'evaluation.json').write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    (output / 'per_user.json').write_text(json.dumps(per_user, ensure_ascii=False, indent=2), encoding='utf-8')
    lines = ['# Resultados experimentais', '', 'Gerado por `python evaluate.py`. Dados de teste nunca entram no modelo.', '',
             f'Treino: {len(train)}; teste: {len(test)}; semente: 42.', '',
             '| Modelo | MAE ↓ | RMSE ↓ | Precision@10 ↑ | Recall@10 ↑ | NDCG@10 ↑ | Cobertura ↑ |',
             '|---|---:|---:|---:|---:|---:|---:|']
    for name, metrics in results.items():
        lines.append('| ' + name + ' | ' + ' | '.join('—' if metrics[k] is None else f'{metrics[k]:.4f}' for k in ('mae', 'rmse', 'precision@10', 'recall@10', 'ndcg@10', 'catalog_coverage@10')) + ' |')
    lines += ['', 'Ranking: média macro apenas dos usuários com ao menos um item relevante no teste. '
              'Relevante = nota ≥ 4; candidatos = todos os filmes observados no treino e desconhecidos do usuário. '
              'Itens não avaliados no teste contam como não acertos, embora possam ser relevantes na prática.', '']
    for example in examples:
        lines += [f"## Usuário {example['user']}", '',
                  f"Histórico de treino: {example['train_size']}; teste: {example['test_size']}; relevantes: {example['relevant_test']}.", '',
                  'Amostra do histórico: ' + '; '.join(f"{r['title']} ({r['rating']}/5)" for r in example['history_sample']) + '.', '',
                  'Métricas: ' + ', '.join(f'{k} = {v:.4f}' for k, v in example['metrics'].items()) + '.', '',
                  '| Filme recomendado | Estimativa | Acerto no teste |', '|---|---:|---|']
        lines += [f"| {r['title']} | {r['score']:.2f} | {'Sim' if r['hit'] else 'Não'} |" for r in example['recommendations']]
        lines += ['']
    lines += ['## Usuário sem histórico', '', 'Recebe a média bayesiana por filme. Não há personalização até existirem evidências suficientes.', '',
              ', '.join(r['title'] for r in payload['cold_start'][:5]) + '.']
    (output / 'RESULTADOS.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(json.dumps(results, indent=2))


if __name__ == '__main__':
    main()
