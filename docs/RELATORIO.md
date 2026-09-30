# CineMatch: recomendação personalizada de filmes por filtragem colaborativa

**Disciplina:** Oficina de Desenvolvimento de Sistemas.  
**Equipe:** Danilo Cavalcante e Rennan Kauê.  
**Data:** 30 de setembro de 2026.

## Resumo

O CineMatch é uma aplicação local para recomendar filmes a partir de avaliações explícitas. O sistema usa filtragem colaborativa baseada em usuários para estimar a nota de filmes ainda desconhecidos e uma média bayesiana para o caso de início frio. Em uma divisão reproduzível por usuário do MovieLens 100K, o modelo colaborativo obteve MAE de 0,7567 e RMSE de 0,9753, menores que a referência de média bayesiana, e Precision@10 de 0,189, acima das referências de mais populares (0,122) e de média bayesiana (0,084). A interface permite consultar histórico, recomendar, registrar avaliações e coletar a percepção de participantes.

## 1. Objetivo e problema

Catálogos extensos tornam a escolha de filmes cansativa. O objetivo foi criar um recomendador que, dado o histórico de notas de uma pessoa, encontre filmes não vistos com maior chance de agradá-la. O sistema deve também continuar útil para uma pessoa sem histórico e possibilitar avaliação por usuários de teste.

## 2. Fundamentação

Na filtragem colaborativa, preferências de pessoas com comportamentos parecidos ajudam a prever preferências ausentes. Para cada usuário-alvo `u`, calculamos a similaridade cosseno entre o vetor de notas centralizado pela média desse usuário e o vetor de cada candidato a vizinho. A predição de um filme `i` é a média do alvo acrescida da média ponderada dos desvios de nota dos vizinhos:

`r̂(u,i) = μu + Σv sim(u,v)(r(v,i) − μv) / Σv |sim(u,v)|`.

Foram usados os 40 vizinhos mais similares, pelo menos dois filmes em comum e regularização `c/(c+10)`, em que `c` é o número de coavaliações. Essas escolhas reduzem a influência de coincidências com pouco suporte.

A nota prevista `r̂(u,i)` é usada para medir o erro de nota, mas não para ordenar a lista. Por ser uma média, ela chega a 5,00 quando um único vizinho avaliou um filme raro com nota máxima, e esses títulos dominavam o topo. A lista Top-10 é ordenada pelos votos dos vizinhos, o numerador da fórmula, `Σv sim(u,v)(r(v,i) − μv)`: o valor cresce com o número de vizinhos parecidos que gostaram do filme, de modo que um consenso de muitos vizinhos vence a opinião isolada de um. Empates, como no início frio, seguem a nota prevista. Quando o perfil tem menos de duas avaliações ou não possui vizinhos utilizáveis, a aplicação ordena filmes por média bayesiana, trazendo primeiro os gêneros que a pessoa declarou, e essa média suaviza a média de cada filme em direção à média global usando peso prévio 20.

## 3. Dados e preparação

Foi usado MovieLens 100K, do GroupLens Research: 100.000 notas de 1 a 5 dadas por 943 usuários a 1.682 filmes entre setembro de 1997 e abril de 1998. Cada usuário tem ao menos 20 avaliações. O arquivo `u.data` contém usuário, item, nota e instante; `u.item` acrescenta título e gêneros.

A preparação remove linhas inválidas, mantém somente notas de 1 a 5 e, se houvesse uma dupla usuário–filme repetida, preservaria a interação mais recente. No arquivo empregado não houve perda: 100.000 interações limpas. A matriz usuário × filme é esparsa e valores ausentes não são convertidos em zero como se fossem uma nota. Os dados são baixados pela fonte oficial e não entram no repositório.

A aplicação web usa o mesmo `Recommender` avaliado, treinado com as 100.000 notas. Perfis criados no site recebem IDs a partir de 1001 e suas notas, gravadas em SQLite, são acrescentadas à matriz a cada nova avaliação; assim, perfis criados no site também passam a servir de vizinhos entre si.

## 4. Método experimental

A semente 42 seleciona cerca de 20% das avaliações de cada usuário para teste, com pelo menos uma avaliação de teste. Restaram 80.367 interações de treino e 19.633 de teste. Nenhuma avaliação de teste aparece no perfil entregue ao modelo. Há duas referências não personalizadas, que entregam a mesma lista a todos: a média bayesiana, que ordena pela nota média suavizada, e os mais populares, que ordena pelo número de avaliações do filme no treino. A segunda é considerada uma referência forte em recomendação e só é comparada nas métricas de ranking, pois não prevê notas.

O critério de ordenação e o número de vizinhos foram escolhidos numa validação tirada apenas do treino: as 80.367 notas de treino foram divididas de novo em 80/20 (semente 7), e as variantes foram comparadas nessa validação. Ordenar pela nota prevista resultou em Precision@10 de 0,013; ordenar pelos votos, 0,124, contra 0,059 da média bayesiana. Entre k = 20, 30, 40, 60, 100, 200 e 400, k = 40 teve a maior Precision@10 e o maior NDCG@10. O conjunto de teste só foi usado uma vez, na medição final abaixo. A comparação é reproduzida por `python validate.py`.

MAE é a média do erro absoluto de notas previstas; RMSE penaliza erros grandes. Para a lista Top-10, um filme do teste é relevante quando a nota real é pelo menos 4. Precision@10 mede a fração de acertos na lista, Recall@10 mede a fração de filmes relevantes encontrados, e NDCG@10 dá mais peso ao acerto nas primeiras posições. Cobertura é a fração do catálogo de treino que apareceu em ao menos uma lista Top-10. As métricas de ranking são médias macro dos 927 usuários que tinham item relevante no teste.

## 5. Resultados

| Modelo | MAE ↓ | RMSE ↓ | Precision@10 ↑ | Recall@10 ↑ | NDCG@10 ↑ | Cobertura@10 ↑ |
|---|---:|---:|---:|---:|---:|---:|
| **User-kNN, ordenado por votos (final)** | **0,7567** | **0,9753** | **0,1888** | **0,1850** | **0,2597** | 0,1606 |
| User-kNN, ordenado pela nota prevista (versão inicial) | 0,7567 | 0,9753 | 0,0193 | 0,0136 | 0,0223 | 0,4945 |
| Mais populares (referência) | — | — | 0,1217 | 0,1247 | 0,1569 | 0,0292 |
| Média bayesiana (referência) | 0,8310 | 1,0344 | 0,0836 | 0,0631 | 0,0980 | 0,0231 |

O método colaborativo reduz MAE em 8,9% e RMSE em 5,7% frente à média bayesiana, portanto estima notas com mais precisão. Nas métricas de Top-10, o modelo final supera a referência mais forte, a dos mais populares, com Precision@10 55% maior (0,189 contra 0,122), Recall@10 48% maior e NDCG@10 66% maior; frente à média bayesiana, a Precision@10 é 2,3 vezes maior. A versão inicial, que ordenava pela nota prevista, ficava abaixo das duas referências em todas as métricas de ranking: a mudança do critério de ordenação multiplicou a Precision@10 por quase 10, sem alterar as notas previstas, e por isso MAE e RMSE são idênticos nas duas linhas.

A cobertura caiu de 49,5% para 16,1% do catálogo, porque o topo deixou de ser ocupado por títulos raros e passou a reunir filmes que muitos vizinhos aprovam. Ainda assim, o modelo recomenda de cinco a sete vezes mais filmes distintos do que as referências, que entregam praticamente a mesma lista a todos. O arquivo `results/evaluation.json` preserva os números brutos, parâmetros, hash do dataset e ambiente de execução.

## 6. Avaliação com usuários de teste

Os usuários de teste são os 943 usuários do MovieLens avaliados sobre as notas separadas para teste: para cada um, o modelo recebe apenas o histórico de treino, gera um Top-10 com filmes desconhecidos e as recomendações são confrontadas com as notas que a pessoa realmente deu. A tabela abaixo mostra os usuários 1 a 5, escolhidos pelo número e não pelo desempenho, com o modelo final.

| Usuário | Treino | Teste | Relevantes no teste | Acertos no Top-10 | Posições dos acertos | Precision@10 | Recall@10 | NDCG@10 |
|---:|---:|---:|---:|---:|---|---:|---:|---:|
| 1 | 218 | 54 | 27 | 4 | 1, 2, 3, 8 | 0,40 | 0,1481 | 0,5384 |
| 2 | 50 | 12 | 8 | 2 | 1, 4 | 0,20 | 0,2500 | 0,3619 |
| 3 | 44 | 10 | 4 | 0 | — | 0,00 | 0,0000 | 0,0000 |
| 4 | 20 | 4 | 1 | 0 | — | 0,00 | 0,0000 | 0,0000 |
| 5 | 140 | 35 | 11 | 3 | 1, 4, 7 | 0,30 | 0,2727 | 0,3882 |

Três dos cinco usuários acertaram logo na primeira posição. Os usuários 3 e 4 não tiveram acertos, mas tinham apenas 4 e 1 filmes relevantes no teste: com tão poucos alvos, errar os dez não significa que a lista seja ruim, e sim que há pouca evidência para medir. Nos 927 usuários com item relevante no teste, 682 (74%) tiveram ao menos um acerto no Top-10, contra 130 (14%) na versão inicial, e um usuário chegou a Precision@10 de 1,0. O histórico, a lista completa e os acertos de cada um dos cinco usuários estão em [`results/RESULTADOS.md`](../results/RESULTADOS.md), e as métricas de todos os usuários em `results/per_user.json`.

Como complemento, a interface registra, abaixo das recomendações, uma nota de utilidade de 1 a 5, se a pessoa assistiria a pelo menos um filme e um comentário opcional. O protocolo está em [`docs/TESTE_COM_USUARIOS.md`](TESTE_COM_USUARIOS.md) e `python feedback_report.py` resume as respostas, permitindo medir a utilidade percebida por pessoas em trabalhos futuros.

## 7. Limitações

Os dados são antigos, contêm só notas explícitas e não representam o público atual. Similaridade baseada em coavaliações sofre com esparsidade e início frio. A nota prevista não é garantia de interesse real e a avaliação offline assume que itens não observados no teste são irrelevantes, o que subestima listas boas. Ordenar por votos favorece filmes que muitos vizinhos avaliaram, o que reduz a cobertura e pode reforçar o viés de popularidade. O algoritmo também não considera contexto, disponibilidade de streaming, idioma ou diversidade intencional.

## 8. Conclusão

O CineMatch cumpre o fluxo de um recomendador: prepara interações, personaliza por filtragem colaborativa, exclui itens conhecidos, atende início frio, permite nova avaliação e coleta feedback. O experimento mostra que o modelo colaborativo supera as referências não personalizadas tanto na previsão de notas quanto no Top-10, inclusive a dos filmes mais populares, e que a forma de ordenar a lista importa tanto quanto a previsão: ordenar pelos votos dos vizinhos, e não pela nota média prevista, multiplicou a precisão por quase 10. Como evolução, a lista pode ser reordenada para aumentar a diversidade sem perder precisão, e a utilidade percebida pode ser medida com participantes pelo formulário já integrado.

## Referências

HARPER, F. M.; KONSTAN, J. A. The MovieLens Datasets: History and Context. *ACM Transactions on Interactive Intelligent Systems*, 5(4), 2015. DOI: 10.1145/2827872.

GROUPLENS RESEARCH. *MovieLens 100K Dataset*. Disponível em: <https://grouplens.org/datasets/movielens/100k/>. Acesso em: 27 set. 2026.
