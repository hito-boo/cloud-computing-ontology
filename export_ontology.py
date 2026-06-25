import json
import re
from typing import Dict, List, Optional

ONTOLOGY_CONTEXT: Dict = {
    "schema": "https://schema.org/",
    "concepts": "http://host/ontology/cloud-computing#", # Placeholder

    "id": "@id",
    "type": "@type",

    "title": "schema:name",
    "authors": {"@id": "schema:author", "@container": "@list"},
    "year": "schema:datePublished",
    "doi": "schema:identifier",
    "journal": "schema:isPartOf",
    "abstract": "schema:abstract",
    "keywords": {"@id": "schema:keywords", "@container": "@list"},

    "objective": {"@id": "concepts:hasObjective", "@container": "@list"},
    "problem": {"@id": "concepts:hasProblem", "@container": "@list"},
    "methodology": {"@id": "concepts:hasMethodology", "@container": "@list"},
    "contributions": {"@id": "concepts:hasContribution", "@container": "@list"},
    "futureWork": {"@id": "concepts:hasFutureWork", "@container": "@list"},

    "references": {"@id": "schema:citation", "@container": "@list"},
}

# Constrói um URN único e estável para um artigo a partir do seu nome
def _make_article_id(filename: str) -> str:
    slug = re.sub(r"\.pdf$", "", filename, flags=re.I)
    slug = re.sub(r"[^a-zA-Z0-9\-]+", "-", slug).strip("-").lower()
    return f"urn:article:{slug}"

# Constrói um nó JSON-LD combinando os campos da categorização e os da extração
def build_article_node(paper: Dict, extraction: Dict) -> Dict:
    meta = paper.get("metadata", {})
    return {
        "id": _make_article_id(paper["filename"]),
        "type": "schema:ScholarlyArticle",

        "title": paper.get("title", ""),
        "authors": paper.get("authors", []),
        "year": meta.get("year", ""),
        "doi": meta.get("doi", ""),
        "journal": meta.get("journal", ""),
        "abstract": paper.get("abstract", ""),
        "keywords": paper.get("keywords", []),

        "objective": extraction.get("objective", []),
        "problem": extraction.get("problem", []),
        "methodology": extraction.get("methodology", []),
        "contributions": extraction.get("contributions", []),
        "futureWork": extraction.get("future_work", []),

        "references": paper.get("references", []),
    }

# Monta o documento completo da ontologia em JSON-LD para o córpus
def build_ontology(categorized_corpus: Dict[str, Dict], stage2_corpus: Dict[str, Dict], corpus_top_terms: Optional[Dict] = None) -> Dict:
    graph: List[Dict] = []
    for filename, paper in categorized_corpus.items():
        stage2 = stage2_corpus.get(filename, {})
        graph.append(build_article_node(paper, stage2))

    ontology: Dict = {
        "@context": ONTOLOGY_CONTEXT,
        "@graph": graph,
    }

    if corpus_top_terms:
        # Armazenar como um anexo simples, pois não é uma entidade do artigo
        ontology["corpusTopTerms"] = corpus_top_terms

    return ontology

# Salva o documento de ontologia como JSON-LD formatado
def save_ontology(ontology: Dict, path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(ontology, f, ensure_ascii=False, indent=2)

# Constrói um resumo breve da ontologia gerada
def ontology_summary(ontology: Dict) -> str:
    graph = ontology.get("@graph", [])
    lines = [
        f"Artigos na ontologia : {len(graph)}",
        f"Contexto (@context)  : {len(ontology.get('@context', {}))} termos mapeados",
    ]
    for node in graph:
        filled = sum(1 for f in ("objective", "problem", "methodology", "contributions", "futureWork") if node.get(f))
        lines.append(
            f"  - {node['id']:55s} | Stage2: {filled}/5 campos | "
            f"refs: {len(node.get('references', []))}"
        )
    return "\n".join(lines)