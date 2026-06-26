"""Modelos de linguagem do corpus: bag-of-words e n-gramas (Etapa 1).

A partir dos tokens gerados na etapa de pre-processamento, este modulo monta
o modelo de bag-of-words e os n-gramas (bigramas, trigramas, etc.) de cada
artigo e do corpus agregado, alem de identificar os termos mais frequentes.
"""

from collections import Counter
from typing import Dict, List, Tuple


def bag_of_words(tokens: List[str]) -> Counter:
    """Constroi o modelo de bag-of-words (contagem de frequencia de cada token)."""
    return Counter(tokens)


def n_grams(tokens: List[str], n: int = 2) -> Counter:
    """Gera os n-gramas da lista de tokens e retorna a frequencia de cada um.

    N-gramas formados por um unico token repetido (ex.: "cloud cloud") sao
    descartados, pois normalmente indicam ruido de tokenizacao.
    """
    if len(tokens) < n:
        return Counter()
    grams = [tuple(tokens[i:i + n]) for i in range(len(tokens) - n + 1) if len(set(tokens[i:i + n])) > 1]
    return Counter(grams)


def paper_language_models(paper_pp: Dict, ns: Tuple[int, ...] = (2, 3)) -> Dict:
    """Calcula o bag-of-words e os n-gramas de um unico artigo pre-processado."""
    tokens = paper_pp["total_tokens"]

    bow = bag_of_words(tokens)
    ngrams_result = {n: n_grams(tokens, n) for n in ns}

    return {
        "filename": paper_pp["filename"],
        "bow": bow,
        "ngrams": ngrams_result,
    }


def aggregate_corpus(corpus_pp: List[Dict], ns: Tuple[int, ...] = (2, 3)) -> Dict:
    """Agrega o bag-of-words e os n-gramas de todos os artigos em contagens globais."""
    bow_global = Counter()
    ngrams_global = {n: Counter() for n in ns}
    per_paper = {}

    for paper_pp in corpus_pp:
        models = paper_language_models(paper_pp, ns=ns)
        bow_global += models["bow"]
        for n in ns:
            ngrams_global[n] += models["ngrams"][n]
        per_paper[paper_pp["filename"]] = models

    return {
        "bow_global": bow_global,
        "ngrams_global": ngrams_global,
        "per_paper": per_paper,
    }


def top_terms(counter: Counter, n: int = 10, ngram_format: bool = False) -> List[Tuple]:
    """Retorna os ``n`` termos (ou n-gramas) mais frequentes de um ``Counter``."""
    most_common = counter.most_common(n)
    if ngram_format:
        most_common = [(" ".join(term), freq) for term, freq in most_common]
    return most_common


def top_terms_corpus(aggregate: Dict, top_n: int = 10) -> Dict:
    """Extrai e formata os unitermos e n-gramas mais frequentes do corpus agregado."""
    result = {"top_uniterms": top_terms(aggregate["bow_global"], top_n)}
    for n, counter in aggregate["ngrams_global"].items():
        key = f"top_{n}gramas"
        result[key] = top_terms(counter, top_n, ngram_format=True)

    return result


def print_top_terms(top: Dict, title: str = "Termos Mais Frequentes do Corpus") -> None:
    """Imprime no console os termos mais frequentes, com uma barra proporcional a frequencia."""
    print(f"\n{'═' * 70}")
    print(f"  {title}")
    print(f"{'═' * 70}")

    labels = {
        "top_uniterms": "Unitermos (BoW)",
        "top_2grams": "Bigramas",
        "top_3grams": "Trigramas",
    }

    for key, terms in top.items():
        print(f"\n  ---- {labels.get(key, key)} ----")
        for rank, (term, freq) in enumerate(terms, 1):
            bar = "█" * min(int(freq / max(t[1] for t in terms) * 30), 30)
            print(f"  {rank:2d}. {term:<35s} {freq:5d}  {bar}")

    print(f"{'═' * 70}\n")
