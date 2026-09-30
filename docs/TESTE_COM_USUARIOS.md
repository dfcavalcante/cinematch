# Protocolo de teste com usuários

## Objetivo

Medir se a lista parece útil para pessoas reais, algo que métricas offline não conseguem responder diretamente.

## Participantes e consentimento

Convide ao menos cinco voluntários adultos. Não colete nome, e-mail nem dados sensíveis: no campo de nome, use códigos P01, P02 etc. Explique: “Esta é uma demonstração acadêmica; suas notas e comentário serão usados apenas de forma agregada no relatório.” A participação é opcional e a pessoa pode parar a qualquer momento.

## Roteiro por participante (5–8 minutos)

1. Com `python app.py` rodando, clique em “+ Novo perfil” e digite o código do participante (P01, P02…) como nome. Anote o ID que o perfil recebe (1001, 1002…), exibido em “Alternar perfil” ao lado do nome.
2. Peça que a pessoa escolha seus gêneros favoritos e avalie de 5 a 10 filmes conhecidos, usando a busca. Não sugira notas.
3. Peça que observe a lista de recomendações.
4. No formulário “Estas recomendações foram úteis?”, abaixo da lista, a própria pessoa marca a utilidade de 1 (nada útil) a 5 (muito útil), responde se assistiria a pelo menos um filme e deixa um comentário opcional.
5. Não altere as respostas posteriormente.

## Como reportar

Depois do último participante, execute:

```powershell
python feedback_report.py
```

O script lê `cinematch.sqlite3` e gera `results/TESTE_USUARIOS.md` com número de respostas, média e desvio-padrão da utilidade, proporção que assistiria a pelo menos um filme e a tabela por perfil com os comentários.

No relatório, acrescente esses números e dois ou três temas dos comentários, sem identificação. Diferencie esse resultado humano da avaliação offline. Não preencha valores sem aplicar o teste.
