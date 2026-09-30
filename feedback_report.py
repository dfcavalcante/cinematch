"""Resume as respostas do formulário de utilidade gravadas pela interface em cinematch.sqlite3."""
import sqlite3
import statistics
from recommender import ROOT

DB = ROOT / 'cinematch.sqlite3'


def main():
    if not DB.exists():
        raise SystemExit('Nenhuma resposta ainda: execute python app.py e aplique o teste com participantes.')
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    rows = con.execute('SELECT f.user_id, f.usefulness, f.would_watch, f.comment, f.created_at, '
                       '(SELECT COUNT(*) FROM user_ratings r WHERE r.user_id = f.user_id) AS rated '
                       'FROM feedback f ORDER BY f.id').fetchall()
    if not rows:
        raise SystemExit('Nenhuma resposta registrada ainda.')
    scores = [row['usefulness'] for row in rows]
    watch = sum(row['would_watch'] for row in rows)
    lines = ['# Teste com usuários', '', 'Gerado por `python feedback_report.py` a partir das respostas enviadas na interface.', '',
             f'Respostas: {len(rows)}; perfis distintos: {len({row["user_id"] for row in rows})}.', '',
             f'Utilidade média: {statistics.mean(scores):.2f} (desvio-padrão {statistics.stdev(scores) if len(scores) > 1 else 0:.2f}), escala de 1 a 5.', '',
             f'Assistiria a pelo menos um filme: {watch}/{len(rows)} ({watch / len(rows):.0%}).', '',
             '| Perfil | Filmes avaliados no site | Utilidade | Assistiria? | Comentário |', '|---:|---:|---:|---|---|']
    lines += [f"| {row['user_id']} | {row['rated']} | {row['usefulness']} | {'Sim' if row['would_watch'] else 'Não'} | {(row['comment'] or '').replace('|', '/')} |" for row in rows]
    output = ROOT / 'results' / 'TESTE_USUARIOS.md'
    output.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print('\n'.join(lines[4:9]))
    print(f'Relatório salvo em {output}')


if __name__ == '__main__':
    main()
