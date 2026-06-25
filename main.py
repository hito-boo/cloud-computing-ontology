from read_papers import read_papers
from categorizer import categorize_corpus, paper_brief
from preprocessor import preprocess_paper
from language_models import aggregate_corpus, top_terms_corpus, print_top_terms
from extractor import extract_corpus, extraction_brief
from export_ontology import build_ontology, save_ontology, ontology_summary
from analysis import generate_all_visualizations
import json

PAPERS_PATH = "Artigos"
CATEGORIZED_OUTPUT = "categorized_output.json"
BRIEF_OUTPUT = "brief_output.txt"
TOP_TERMS_OUTPUT = "top_terms_output.txt"
EXTRACTION_OUTPUT = "extraction_output.json"
ONTOLOGY_OUTPUT = "ontology_corpus.jsonld"

# Leitura
print("=" * 60)
print("[1] Lendo PDFs...")
raw_papers = read_papers(PAPERS_PATH)
print(f"    {len(raw_papers)} artigos lidos.\n")

# Categorização
print("[2] Categorizando artigos...")
categorized = categorize_corpus(raw_papers)

# Salva JSON com a estrutura completa
with open(CATEGORIZED_OUTPUT, "w", encoding="utf-8") as f:
    json.dump(categorized, f, ensure_ascii=False, indent=2)
print(f"    Estrutura salva em '{CATEGORIZED_OUTPUT}'\n")

# Resumo textual
with open(BRIEF_OUTPUT, "w", encoding="utf-8") as f:
    for name, paper in categorized.items():
        f.write(paper_brief(paper))
        f.write("\n" + "-" * 60 + "\n\n")
print(f"    Resumo salvo em '{BRIEF_OUTPUT}'\n")

# Exibe resumo no console
print("    Resumo por artigo:")
for name, paper in categorized.items():
    print()
    for line in paper_brief(paper).split("\n"):
        print(f"    {line}")

# Pré-Processamento
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

# Modelos de linguagem e termos mais frequentes
print("\n[4] Gerando modelos de linguagem (BoW + Bigramas + Trigramas)...")
aggregated = aggregate_corpus(corpus_pp, ns=(2, 3))
top = top_terms_corpus(aggregated, top_n=10)

# Salva e exibe
import io, sys
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

# Referências extraídas
print("\n[5] Referências extraídas por artigo:")
total_refs = 0
for name, paper in categorized.items():
    n = len(paper["references"])
    total_refs += n
    print(f"    {name}: {n} referências")
    for ref in paper["references"][:2]:
        print(f"      • {ref[:90]}...")

print(f"\n    Total: {total_refs} referências no corpus.")

# Extrai Objetivo, Problema, Metodologia e Contribuições
print("\n[6] Extraindo objetivo, problema, metodologia e contribuicoes...")
extracted_corpus = extract_corpus(categorized)

with open(EXTRACTION_OUTPUT, "w", encoding="utf-8") as f:
    json.dump(extracted_corpus, f, ensure_ascii=False, indent=2)

for filename, info in extracted_corpus.items():
    print()
    print(extraction_brief(filename, info))

# Constrói Ontologia JSON-LD
print("\n[7] Construindo ontologia JSON-LD do córpus...")
corpus_top_terms = {
    "top_uniterms": top.get("top_uniterms", []),
    "top_bigrams": top.get("top_2gramas", []),
    "top_trigrams": top.get("top_3gramas", [])
}

ontology = build_ontology(categorized, extracted_corpus, corpus_top_terms)
save_ontology(ontology, ONTOLOGY_OUTPUT)

print(ontology_summary(ontology))
print(f"\nOntologia salva em '{ONTOLOGY_OUTPUT}'")

# [8] Visualizações Analíticas
print("\n[8] Gerando visualizações analíticas...")

# Extrai os tokens gerados na etapa de pré-processamento para o formato exigido
tokens_dict = {pp["filename"]: pp["total_tokens"] for pp in corpus_pp}

generate_all_visualizations(
    categorized_corpus=categorized,
    stage2_corpus=extracted_corpus,
    tokens_per_article=tokens_dict,
    output_dir="visualizations"
)