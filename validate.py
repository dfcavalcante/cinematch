"""Escolha do critério de ordenação e de k numa validação tirada só do treino; o teste não é usado."""
import numpy as np
from recommender import Recommender, load_data
from evaluate import split_data, ranking_metrics


def rank_scores(model, user, k, by_votes):
    """Repete o cálculo de vizinhança do Recommender, variando k e o critério de ordenação."""
    row = model.matrix[model.user_index[user]]
    known = row > 0
    mean = row[known].mean()
    centered = np.where(known, row - mean, 0)
    denominator = model.norms * np.linalg.norm(centered)
    sim = np.divide(model.centered @ centered, denominator, out=np.zeros(len(model.users)), where=denominator > 0)
    common = model.mask @ known.astype(float)
    sim *= common / (common + model.shrinkage)
    sim[common < 2] = 0
    sim[model.user_index[user]] = 0
    neighbors = np.argsort(-sim, kind='stable')[:k]
    neighbors = neighbors[sim[neighbors] > 0]
    weights = sim[neighbors]
    totals, votes = weights @ model.mask[neighbors], weights @ model.centered[neighbors]
    if by_votes:
        return votes
    return np.where(totals > 0, np.clip(mean + np.divide(votes, totals, out=np.zeros_like(votes), where=totals > 0), 1, 5), model.baseline)


def precision(model, valid, scorer):
    values = []
    for user in model.users:
        relevant = {int(m) for _, m, r, _ in valid[valid[:, 0] == user] if r >= 4}
        if not relevant:
            continue
        scores = scorer(user)
        candidates = np.flatnonzero((model.matrix[model.user_index[user]] == 0) & (model.item_counts > 0))
        top = model.items[candidates[np.lexsort((model.items[candidates], -scores[candidates]))][:10]]
        values.append(ranking_metrics([int(m) for m in top], relevant))
    return np.mean([v['precision@10'] for v in values]), np.mean([v['ndcg@10'] for v in values])


def main():
    movies, ratings, _ = load_data()
    train, _ = split_data(ratings)          # mesmo treino do evaluate.py
    fit, valid = split_data(train, seed=7)  # validação dentro do treino
    model = Recommender(movies, fit)
    p, ndcg = precision(model, valid, lambda user: model.baseline)
    print(f'{"média bayesiana":<28} Precision@10={p:.4f}  NDCG@10={ndcg:.4f}')
    p, ndcg = precision(model, valid, lambda user: rank_scores(model, user, 40, by_votes=False))
    print(f'{"k=40, nota prevista":<28} Precision@10={p:.4f}  NDCG@10={ndcg:.4f}')
    for k in (20, 30, 40, 60, 100, 200, 400):
        p, ndcg = precision(model, valid, lambda user: rank_scores(model, user, k, by_votes=True))
        print(f'{f"k={k}, votos":<28} Precision@10={p:.4f}  NDCG@10={ndcg:.4f}', flush=True)


if __name__ == '__main__':
    main()
