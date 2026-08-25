#!/usr/bin/env python3
"""Valida o index.json do aresy-index num Pull Request."""
import json
import os
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INDEX_PATH = os.path.join(REPO_ROOT, "index.json")


def load_json_no_dupes(path):
    seen = {}

    def hook(pairs):
        for k, v in pairs:
            if k in seen:
                raise ValueError(f"chave duplicada no index.json: '{k}'")
            seen[k] = v
        return dict(pairs)

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f, object_pairs_hook=hook)


def load_base_index():
    try:
        out = subprocess.run(
            ["git", "show", "origin/main:index.json"],
            cwd=REPO_ROOT, capture_output=True, text=True, check=True,
        )
        return json.loads(out.stdout)
    except Exception:
        return {}


def main():
    errors = []
    warnings = []

    if not os.path.isfile(INDEX_PATH):
        print("ERRO: index.json não encontrado na raiz do repositório.")
        sys.exit(1)

    try:
        index = load_json_no_dupes(INDEX_PATH)
    except ValueError as e:
        print(f"ERRO: {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"ERRO: index.json não é um JSON válido: {e}")
        sys.exit(1)

    if not isinstance(index, dict):
        print("ERRO: index.json precisa ser um objeto {nome: caminho, ...}")
        sys.exit(1)

    base_index = load_base_index()

    for name, entry in index.items():
        if not isinstance(entry, str):
            errors.append(f"'{name}': valor precisa ser uma string (caminho ou URL)")
            continue

        if entry.startswith("http://") or entry.startswith("https://"):
            if not entry.endswith(".ay"):
                errors.append(f"'{name}': URL externa não termina em .ay ({entry})")
            continue

        if not entry.endswith(".ay"):
            errors.append(f"'{name}': caminho não termina em .ay ({entry})")
            continue

        full_path = os.path.join(REPO_ROOT, entry)
        if not os.path.isfile(full_path):
            errors.append(f"'{name}': arquivo não encontrado ({entry})")
            continue

        filename = os.path.basename(entry)
        expected = f"{name}.ay"
        if filename != expected:
            errors.append(
                f"'{name}': o arquivo se chama '{filename}', mas deveria se chamar "
                f"'{expected}' (nome do arquivo precisa bater com a chave do index.json)"
            )

        expected_prefix = f"packages/{name}/"
        if not entry.startswith(expected_prefix):
            errors.append(
                f"'{name}': esperava o caminho começando com '{expected_prefix}' "
                f"(veio '{entry}') — cada pacote fica na sua própria pasta"
            )

        if name in base_index and base_index[name] != entry:
            warnings.append(
                f"'{name}': já existia no index.json (apontando pra "
                f"'{base_index[name]}') e este PR muda pra '{entry}'. "
                "Confirma se quem abriu o PR é o dono original do pacote."
            )

    if warnings:
        print("Avisos (não bloqueiam o PR, mas pedem atenção na revisão):")
        for w in warnings:
            print(f"  - {w}")
        print()

    if errors:
        print("Erros encontrados:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)

    print(f"OK: index.json válido, {len(index)} pacote(s) conferido(s).")


if __name__ == "__main__":
    main()
