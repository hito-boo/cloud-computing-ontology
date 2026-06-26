"""Script utilitario para baixar manualmente os recursos do NLTK usados no projeto.

O modulo ``pipeline.preprocessing`` ja baixa esses recursos automaticamente
na primeira execucao (se ainda nao estiverem em cache local). Este script
existe apenas como atalho para preparar o ambiente antecipadamente, por
exemplo em uma maquina nova ou em um ambiente de CI sem acesso a rede
durante a execucao do pipeline principal.

Uso:
    python scripts/download_nltk_resources.py
"""

import nltk

if __name__ == "__main__":
    for resource in ["stopwords", "wordnet", "omw-1.4"]:
        nltk.download(resource)
