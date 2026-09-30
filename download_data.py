"""Baixa arquivos oficiais sem redistribuir o dataset no repositório."""
from pathlib import Path
from urllib.request import urlopen
import hashlib
import json

ROOT = Path(__file__).resolve().parent
BASE = 'https://files.grouplens.org/datasets/movielens/ml-100k/'


def main():
    target = ROOT / 'data' / 'ml-100k'
    target.mkdir(parents=True, exist_ok=True)
    manifest = {}
    for name in ('u.data', 'u.item', 'u.genre', 'README'):
        path = target / name
        if not path.exists():
            print(f'Baixando {name}...', flush=True)
            with urlopen(BASE + name, timeout=60) as response:
                content = response.read()
            temporary = path.with_suffix('.tmp')
            temporary.write_bytes(content)
            temporary.replace(path)
        manifest[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    (target / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print('Dataset disponível em data/ml-100k. Leia README para os termos de uso.')


if __name__ == '__main__':
    main()
