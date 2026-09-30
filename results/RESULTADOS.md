# Resultados experimentais

Gerado por `python evaluate.py`. Dados de teste nunca entram no modelo.

Treino: 80367; teste: 19633; semente: 42.

| Modelo | MAE ↓ | RMSE ↓ | Precision@10 ↑ | Recall@10 ↑ | NDCG@10 ↑ | Cobertura ↑ |
|---|---:|---:|---:|---:|---:|---:|
| user_knn | 0.7567 | 0.9753 | 0.1888 | 0.1850 | 0.2597 | 0.1606 |
| media_bayesiana | 0.8310 | 1.0344 | 0.0836 | 0.0631 | 0.0980 | 0.0231 |
| mais_populares | — | — | 0.1217 | 0.1247 | 0.1569 | 0.0292 |

Ranking: média macro apenas dos usuários com ao menos um item relevante no teste. Relevante = nota ≥ 4; candidatos = todos os filmes observados no treino e desconhecidos do usuário. Itens não avaliados no teste contam como não acertos, embora possam ser relevantes na prática.

## Usuário 1

Histórico de treino: 218; teste: 54; relevantes: 27.

Amostra do histórico: Star Trek: First Contact (1996) (4/5); Smilla's Sense of Snow (1997) (2/5); Doom Generation, The (1995) (2/5); Field of Dreams (1989) (3/5); Glengarry Glen Ross (1992) (4/5).

Métricas: precision@10 = 0.4000, recall@10 = 0.1481, ndcg@10 = 0.5384.

| Filme recomendado | Estimativa | Acerto no teste |
|---|---:|---|
| Silence of the Lambs, The (1991) | 4.68 | Sim |
| Alien (1979) | 4.49 | Sim |
| Blade Runner (1982) | 4.41 | Sim |
| Apocalypse Now (1979) | 4.77 | Não |
| Casablanca (1942) | 4.72 | Não |
| Schindler's List (1993) | 4.43 | Não |
| Glory (1989) | 4.46 | Não |
| Apollo 13 (1995) | 4.27 | Sim |
| Rear Window (1954) | 4.75 | Não |
| One Flew Over the Cuckoo's Nest (1975) | 4.35 | Não |

## Usuário 2

Histórico de treino: 50; teste: 12; relevantes: 8.

Amostra do histórico: Mrs. Brown (Her Majesty, Mrs. Brown) (1997) (4/5); Air Force One (1997) (4/5); Bed of Roses (1996) (3/5); English Patient, The (1996) (4/5); Men in Black (1997) (4/5).

Métricas: precision@10 = 0.2000, recall@10 = 0.2500, ndcg@10 = 0.3619.

| Filme recomendado | Estimativa | Acerto no teste |
|---|---:|---|
| L.A. Confidential (1997) | 4.63 | Sim |
| Lone Star (1996) | 4.70 | Não |
| Boot, Das (1981) | 4.98 | Não |
| Good Will Hunting (1997) | 4.78 | Sim |
| Dead Man Walking (1995) | 4.38 | Não |
| Return of the Jedi (1983) | 4.20 | Não |
| Beautiful Thing (1996) | 5.00 | Não |
| Princess Bride, The (1987) | 4.73 | Não |
| Big Night (1996) | 4.36 | Não |
| When We Were Kings (1996) | 4.78 | Não |

## Usuário 3

Histórico de treino: 44; teste: 10; relevantes: 4.

Amostra do histórico: L.A. Confidential (1997) (2/5); Wedding Singer, The (1998) (3/5); Schindler's List (1993) (4/5); In the Name of the Father (1993) (2/5); Paradise Lost: The Child Murders at Robin Hood Hills (1996) (5/5).

Métricas: precision@10 = 0.0000, recall@10 = 0.0000, ndcg@10 = 0.0000.

| Filme recomendado | Estimativa | Acerto no teste |
|---|---:|---|
| Good Will Hunting (1997) | 3.60 | Não |
| Full Monty, The (1997) | 3.45 | Não |
| Star Wars (1977) | 3.69 | Não |
| Apt Pupil (1998) | 3.81 | Não |
| Titanic (1997) | 3.27 | Não |
| Godfather, The (1972) | 3.82 | Não |
| Mrs. Brown (Her Majesty, Mrs. Brown) (1997) | 3.64 | Não |
| Fargo (1996) | 3.50 | Não |
| Back to the Future (1985) | 3.59 | Não |
| Leaving Las Vegas (1995) | 3.61 | Não |

## Usuário 4

Histórico de treino: 20; teste: 4; relevantes: 1.

Amostra do histórico: Mimic (1997) (3/5); Assignment, The (1997) (5/5); One Flew Over the Cuckoo's Nest (1975) (4/5); In & Out (1997) (5/5); Scream (1996) (4/5).

Métricas: precision@10 = 0.0000, recall@10 = 0.0000, ndcg@10 = 0.0000.

| Filme recomendado | Estimativa | Acerto no teste |
|---|---:|---|
| L.A. Confidential (1997) | 5.00 | Não |
| Godfather, The (1972) | 5.00 | Não |
| Titanic (1997) | 5.00 | Não |
| Fargo (1996) | 5.00 | Não |
| Pulp Fiction (1994) | 5.00 | Não |
| Eve's Bayou (1997) | 5.00 | Não |
| Good Will Hunting (1997) | 5.00 | Não |
| Rear Window (1954) | 5.00 | Não |
| As Good As It Gets (1997) | 5.00 | Não |
| Singin' in the Rain (1952) | 5.00 | Não |

## Usuário 5

Histórico de treino: 140; teste: 35; relevantes: 11.

Amostra do histórico: Adventures of Priscilla, Queen of the Desert, The (1994) (5/5); Blues Brothers, The (1980) (5/5); Beverly Hills Cop III (1994) (2/5); Body Snatcher, The (1945) (3/5); Santa Clause, The (1994) (1/5).

Métricas: precision@10 = 0.3000, recall@10 = 0.2727, ndcg@10 = 0.3882.

| Filme recomendado | Estimativa | Acerto no teste |
|---|---:|---|
| Star Wars (1977) | 4.40 | Sim |
| Terminator, The (1984) | 3.70 | Não |
| Terminator 2: Judgment Day (1991) | 3.77 | Não |
| Alien (1979) | 3.60 | Sim |
| Shawshank Redemption, The (1994) | 3.95 | Não |
| Braveheart (1995) | 3.77 | Não |
| Wrong Trousers, The (1993) | 4.36 | Sim |
| Indiana Jones and the Last Crusade (1989) | 3.45 | Não |
| Casablanca (1942) | 3.99 | Não |
| Godfather, The (1972) | 3.64 | Não |

## Usuário sem histórico

Recebe a média bayesiana por filme. Não há personalização até existirem evidências suficientes.

Schindler's List (1993), Casablanca (1942), Shawshank Redemption, The (1994), Star Wars (1977), Wrong Trousers, The (1993).
