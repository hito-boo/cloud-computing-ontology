"""Ponto de entrada do pipeline de PLN sobre o corpus de artigos cientificos.

Executa, em sequencia, todas as etapas do trabalho:

    1. Leitura dos PDFs e extracao de texto bruto
    2. Categorizacao (titulo, autores, secoes e referencias de cada artigo)
    3. Pre-processamento (normalizacao, stop-words, lematizacao)
    4. Modelos de linguagem (bag-of-words, bigramas, trigramas) e termos mais frequentes
    5. Extracao de objetivo, problema, metodologia e contribuicoes (Etapa 2)
    6. Exportacao da ontologia do corpus em JSON-LD (Etapa 3)
    7. Geracao das visualizacoes analiticas do corpus

Uso:
    python main.py
"""

import io
import json
import os
import sys

from pipeline.categorization import categorize_corpus, paper_brief
from pipeline.extraction import extract_corpus, extraction_brief
from pipeline.language_models import aggregate_corpus, print_top_terms, top_terms_corpus
from pipeline.ontology_export import build_ontology, ontology_summary, save_ontology
from pipeline.preprocessing import preprocess_paper
from pipeline.reading import read_papers
from pipeline.visualization import generate_all_visualizations

PAPERS_PATH = "data/Artigos"
OUTPUT_DIR = "output"
PAPERS_PATH_DEMONSTRACAO = "data/Demonstracao"
OUTPUT_DIR_DEMONSTRACAO = "output_demonstracao"
VISUALIZATIONS_DIR = os.path.join(OUTPUT_DIR, "visualizations")

CATEGORIZED_OUTPUT = os.path.join(OUTPUT_DIR, "categorized_output.json")
BRIEF_OUTPUT = os.path.join(OUTPUT_DIR, "brief_output.txt")
TOP_TERMS_OUTPUT = os.path.join(OUTPUT_DIR, "top_terms_output.txt")
EXTRACTION_OUTPUT = os.path.join(OUTPUT_DIR, "extraction_output.json")
ONTOLOGY_OUTPUT = os.path.join(OUTPUT_DIR, "ontology_corpus.jsonld")

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Etapa 1a - Leitura dos PDFs
print("=" * 60)
print("[1] Lendo PDFs...")
raw_papers = read_papers(PAPERS_PATH)
print(f"    {len(raw_papers)} artigos lidos.\n")

# Etapa 1b - Categorizacao (titulo, autores, secoes, referencias)
print("[2] Categorizando artigos...")
categorized = categorize_corpus(raw_papers)

with open(CATEGORIZED_OUTPUT, "w", encoding="utf-8") as f:
    json.dump(categorized, f, ensure_ascii=False, indent=2)
print(f"    Estrutura salva em '{CATEGORIZED_OUTPUT}'\n")

with open(BRIEF_OUTPUT, "w", encoding="utf-8") as f:
    for name, paper in categorized.items():
        f.write(paper_brief(paper))
        f.write("\n" + "-" * 60 + "\n\n")
print(f"    Resumo salvo em '{BRIEF_OUTPUT}'\n")

print("    Resumo por artigo:")
for name, paper in categorized.items():
    print()
    for line in paper_brief(paper).split("\n"):
        print(f"    {line}")

# Etapa 1c - Pre-processamento de texto
print("\n[3] Pré-processando textos...")
corpus_pp = []
for name, paper in categorized.items():
    paper_pp = preprocess_paper(
        paper,
        apply_lemmatizer=True,
        apply_stemming=False,
    )
    corpus_pp.append(paper_pp)
    n_tokens = len(paper_pp["total_tokens"])
    print(f"    {name}: {n_tokens} tokens após pré-processamento")

# Etapa 1d - Modelos de linguagem e termos mais frequentes
print("\n[4] Gerando modelos de linguagem (BoW + Bigramas + Trigramas)...")
aggregated = aggregate_corpus(corpus_pp, ns=(2, 3))
top = top_terms_corpus(aggregated, top_n=10)

buf = io.StringIO()
old_stdout = sys.stdout
sys.stdout = buf

print_top_terms(top, title="10 Termos mais frequentes do córpus - Cloud Computing e Segurança")

sys.stdout = old_stdout
result_top = buf.getvalue()
print(result_top)
with open(TOP_TERMS_OUTPUT, "w", encoding="utf-8") as f:
    f.write(result_top)
print(f"    Termos mais frequentes salvos em '{TOP_TERMS_OUTPUT}'")

# Etapa 1e - Referencias extraidas
print("\n[5] Referências extraídas por artigo:")
total_refs = 0
for name, paper in categorized.items():
    n = len(paper["references"])
    total_refs += n
    print(f"    {name}: {n} referências")
    for ref in paper["references"][:2]:
        print(f"      • {ref[:90]}...")

print(f"\n    Total: {total_refs} referências no corpus.")

# Etapa 2 - Objetivo, problema, metodologia e contribuicoes
print("\n[6] Extraindo objetivo, problema, metodologia e contribuicoes...")
extracted_corpus = extract_corpus(categorized)

with open(EXTRACTION_OUTPUT, "w", encoding="utf-8") as f:
    json.dump(extracted_corpus, f, ensure_ascii=False, indent=2)

for filename, info in extracted_corpus.items():
    print()
    print(extraction_brief(filename, info))

# Etapa 3 - Ontologia do corpus em JSON-LD
print("\n[7] Construindo ontologia JSON-LD do córpus...")
corpus_top_terms = {
    "top_uniterms": top.get("top_uniterms", []),
    "top_bigrams": top.get("top_2gramas", []),
    "top_trigrams": top.get("top_3gramas", []),
}

ontology = build_ontology(categorized, extracted_corpus, corpus_top_terms)
save_ontology(ontology, ONTOLOGY_OUTPUT)

print(ontology_summary(ontology))
print(f"\nOntologia salva em '{ONTOLOGY_OUTPUT}'")

# Visualizacoes analiticas do corpus
print("\n[8] Gerando visualizações analíticas...")

tokens_dict = {pp["filename"]: pp["total_tokens"] for pp in corpus_pp}

generate_all_visualizations(
    categorized_corpus=categorized,
    stage2_corpus=extracted_corpus,
    tokens_per_article=tokens_dict,
    output_dir=VISUALIZATIONS_DIR,
)
