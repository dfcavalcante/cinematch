# CineMatch — recomendador colaborativo de filmes

Aplicação web local que recomenda filmes por filtragem colaborativa baseada em usuários (user-kNN), implementada do zero com NumPy. A base de interações é o MovieLens 100K: 100.000 notas de 943 usuários para 1.682 filmes. O algoritmo que roda na interface é o mesmo avaliado em `evaluate.py`.

## Funcionalidades

- consulta de qualquer um dos 943 usuários do MovieLens: histórico de notas e Top-10 recomendado;
- criação de perfil próprio com nome, gêneros favoritos e, opcionalmente, filmes avaliados;
- recomendações sem filmes que o usuário já avaliou;
- filtragem colaborativa com similaridade cosseno sobre notas centralizadas, 40 vizinhos, mínimo de 2 filmes em comum e redução de similaridades com pouco suporte;
- lista ordenada pelos votos dos vizinhos (quantos gostaram e quanto), para que um filme raro avaliado por um único vizinho não domine o topo;
- início frio: perfil com menos de 2 notas recebe a média bayesiana da comunidade, priorizando os gêneros declarados;
- novas avaliações persistidas em SQLite e incorporadas à matriz na hora — perfis do site passam a servir de vizinhos uns aos outros;
- formulário de utilidade (1–5, “assistiria a pelo menos um?” e comentário) para o teste com participantes;
- experimento reproduzível com MAE, RMSE, Precision@10, Recall@10, NDCG@10 e cobertura, comparado às referências de mais populares e de média bayesiana.

## Como executar

Pré-requisitos: Python 3.10 ou superior, Git e acesso à internet no primeiro uso, para baixar o dataset. A única dependência externa é NumPy (2.1 ou superior, definida em `requirements.txt`); o resto usa apenas a biblioteca padrão. A instalação e os números de `results/` foram verificados em Python 3.10.11 com NumPy 2.1.3 e em Python 3.13.14 com NumPy 2.4.5.

```powershell
git clone https://github.com/dfcavalcante/cinematch.git
cd cinematch
python -m venv .venv
.venv\Scripts\activate          # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python download_data.py   # baixa o MovieLens 100K da fonte oficial para data/ml-100k
python app.py             # http://localhost:8000
```

No Linux/macOS, use `python3` no lugar de `python` se for o nome do interpretador. O MovieLens não é redistribuído neste repositório: `download_data.py` baixa os arquivos do site do GroupLens, junto com o README que traz os termos de uso.

Na página inicial, abra um usuário do MovieLens (1 a 943) ou crie seu perfil. Perfis criados no site recebem IDs a partir de 1001, sem colidir com os usuários da base.

## Estrutura

| Caminho | Finalidade |
|---|---|
| `recommender.py` | carga, preparação e algoritmo user-kNN |
| `app.py` | servidor e API local; une MovieLens e avaliações do site; grava em `cinematch.sqlite3` |
| `web/` | interface HTML, CSS e JavaScript |
| `evaluate.py` | divisão treino/teste e métricas reproduzíveis |
| `validate.py` | escolha do critério de ordenação e do número de vizinhos numa validação tirada só do treino |
| `feedback_report.py` | resume as respostas do formulário de utilidade em `results/TESTE_USUARIOS.md` |
| `results/RESULTADOS.md` | números do experimento e cinco exemplos de usuários |
| `results/evaluation.json` | números brutos, parâmetros, hash do dataset e ambiente de execução |
| `results/per_user.json` | métricas de ranking de cada usuário, para os três modelos |
| `docs/RELATORIO.md` | relatório acadêmico |
| `docs/TESTE_COM_USUARIOS.md` | protocolo opcional para avaliar a utilidade com participantes |

## Reproduzir a avaliação

`python evaluate.py` fixa a semente em 42 e separa, para cada usuário, aproximadamente 80% das avaliações para treino e 20% para teste. A divisão impede que uma avaliação de teste seja usada para treinar ou para compor o histórico do usuário. O user-kNN é comparado a duas referências não personalizadas: a média bayesiana, que também prevê notas, e os filmes mais populares (mais avaliados no treino), que só entra nas métricas de ranking. Os arquivos gerados em `results/` registram parâmetros, hash SHA-256 de `u.data`, ambiente e resultados individuais.

`python validate.py` mostra como foram escolhidos o critério de ordenação (votos dos vizinhos em vez da nota prevista) e k = 40: as notas de treino são divididas de novo em 80/20 e as variantes são comparadas nessa validação, sem tocar no teste.

A interface usa as 100.000 notas completas, enquanto a avaliação treina com 80%. Por isso as recomendações do usuário 1 na tela diferem das listadas em `results/RESULTADOS.md`, embora o algoritmo e os parâmetros sejam idênticos.

Para não tratar itens desconhecidos como negativos de forma incorreta, a interpretação das métricas de ranking é conservadora: apenas filmes com nota real ≥ 4 no teste contam como relevantes; todo item recomendado que não aparece nessa lista deixa de contar como acerto, ainda que o usuário pudesse gostar dele.
