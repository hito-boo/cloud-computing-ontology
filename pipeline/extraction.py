"""Extracao de objetivo, problema, metodologia, contribuicoes e trabalhos
futuros de cada artigo, por casamento de padroes em frases (Etapa 2).

A extracao trabalha em tres zonas do texto do artigo: introducao+abstract
(onde normalmente aparecem objetivo e problema), corpo do texto (onde
aparecem metodologia e contribuicoes) e conclusao (onde normalmente aparecem
os trabalhos futuros).
"""

import re
from typing import Dict, List, Optional

_ABBREVIATIONS = [
    "e.g.", "i.e.", "et al.", "etc.", "vs.", "cf.", "approx.",
    "Fig.", "fig.", "Eq.", "eq.", "Sec.", "sec.", "No.", "no.",
    "Dr.", "Mr.", "Mrs.", "Ms.", "Prof.", "resp.", "Eqs.", "Figs.",
]
_INITIAL_RE = re.compile(r"\b([A-Z])\.\s+(?=[A-Z][a-z])")
_SPLIT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z(])")
_WHITESPACE_RE = re.compile(r"\s+")


def split_sentences(text: str) -> List[str]:
    """Divide um texto em frases, protegendo abreviacoes e iniciais de nomes.

    Como o ponto final tambem aparece em abreviacoes comuns ("e.g.", "et
    al.") e em iniciais de nomes ("J. Silva"), essas ocorrencias sao
    temporariamente substituidas por marcadores antes da divisao por frase,
    e restauradas depois.
    """
    if not text:
        return []

    protected = text
    placeholders: Dict[str, str] = {}
    for i, abbr in enumerate(_ABBREVIATIONS):
        token = f"@@ABBR{i}@@"
        placeholders[token] = abbr
        protected = re.sub(re.escape(abbr), token, protected, flags=re.I)

    protected = _INITIAL_RE.sub(lambda m: f"{m.group(1)}@@DOT@@ ", protected)

    raw_sentences = _SPLIT_RE.split(protected)

    sentences: List[str] = []
    for s in raw_sentences:
        s = s.replace("@@DOT@@", ".")
        for token, abbr in placeholders.items():
            s = s.replace(token, abbr)
        s = _WHITESPACE_RE.sub(" ", s).strip()
        if s:
            sentences.append(s)
    return sentences


_OBJECTIVE_PATTERNS = [
    re.compile(
        r"\b(?:main\s+|primary\s+|overall\s+|key\s+)?"
        r"(?:objective|aim|goal|purpose)s?\s+of\s+(?:this|the)\s+"
        r"(?:article|paper|study|work|research)\s+(?:is|are)\s+to\b", re.I,
    ),
    re.compile(r"\bthis\s+(?:article|paper|study|work|research)\s+aims?\s+to\b", re.I),
    re.compile(r"\bwe\s+aim\s+to\b", re.I),
    re.compile(
        r"\bthe\s+(?:purpose|goal|objective)\s+of\s+this\s+"
        r"(?:article|paper|study|work)\s+is\b", re.I,
    ),
]

# Padroes alternativos, mais amplos, usados quando as regras especificas
# acima nao encontram nenhuma frase de objetivo no artigo
_OBJECTIVE_PATTERNS_BROAD = [
    re.compile(
        r"\bin\s+this\s+(?:paper|article|study|work),?\s+we\s+"
        r"(?:propose|present|introduce|investigate|study|examine|address|"
        r"explore|develop|design|look\s+at|intend\s+to|seek\s+to)\b", re.I,
    ),
    re.compile(
        r"\bthis\s+(?:paper|article|study|work)\s+"
        r"(?:proposes|presents|introduces|investigates|examines|addresses|"
        r"explores|develops|focuses\s+on)\b", re.I,
    ),
    re.compile(r"\bwe\s+(?:propose|present|introduce)\s+a\s+(?:novel|new)\b", re.I),
]

_PROBLEM_PRIMARY_RE = re.compile(r"\bproblems?\b", re.I)
_PROBLEM_SECONDARY_RE = re.compile(
    r"\b(?:challenge|issue|gap|limitation)s?\b.{0,60}"
    r"\b(?:address|addresses|addressed|solve|solves|solved|"
    r"overcome|overcomes|overcame|tackle|tackles|tackled|"
    r"remain|remains|arise|arises|face|faces|faced)\b", re.I,
)

_METHODOLOGY_PATTERNS = [
    re.compile(r"\b(?:method|methodology|approach|framework|technique)s?\b", re.I),
    re.compile(r"\binterviews?\s+(?:was|were)\s+conducted\b", re.I),
    re.compile(r"\bsurveys?\s+(?:was|were)\s+conducted\b", re.I),
    re.compile(r"\bcontent\s+analysis\b", re.I),
    re.compile(r"\bcase\s+stud(?:y|ies)\b", re.I),
    re.compile(r"\bexperiments?\s+(?:was|were)\s+conducted\b", re.I),
    re.compile(
        r"\bwe\s+(?:use|used|employ|employed|adopt|adopted|propose|proposed|"
        r"develop|developed|implement|implemented|evaluate|evaluated|conduct|conducted)\b"
        r".{0,40}\b(?:method|approach|framework|technique|algorithm|model|scheme)\b", re.I,
    ),
    re.compile(r"\bdataset\b", re.I),
]

_CONTRIBUTION_RE = re.compile(r"\bcontribut(?:es|ed|e|ing)\s+to\b", re.I)
_CONTRIBUTION_PATTERNS_BROAD = [
    re.compile(
        r"\b(?:main|key|major|primary|significant)?\s*contributions?\s+of\s+"
        r"(?:this|the)\s+(?:paper|article|study|work)\b", re.I,
    ),
]

_CREDIT_BOILERPLATE_RE = re.compile(r"\bCRediT\s+authorship\s+contribution\s+statement\b", re.I)

_FUTURE_WORK_PATTERNS = [
    re.compile(r"\bfuture\s+(?:work|research|directions?)\b", re.I),
    re.compile(r"\bwe\s+plan\s+to\b", re.I),
    re.compile(r"\bfurther\s+work\b", re.I),
    re.compile(r"\bremains?\s+(?:to\s+be|as\s+(?:a|an)\s+open)\b", re.I),
    re.compile(r"\bopen\s+(?:problem|issue|question)s?\b", re.I),
    re.compile(r"\bcurrently\s+working\s+on\b", re.I),
]


def _find_matches(
    sentences: List[str],
    patterns: List[re.Pattern],
    max_results: int = 3,
    exclude: Optional[set] = None,
) -> List[str]:
    """Procura, em ordem, as primeiras frases que casam com algum dos padroes dados."""
    exclude = exclude or set()
    matches: List[str] = []
    seen: set = set()
    for sent in sentences:
        if sent in exclude or sent in seen:
            continue
        for pat in patterns:
            if pat.search(sent):
                matches.append(sent)
                seen.add(sent)
                break
        if len(matches) >= max_results:
            break
    return matches


def extract_objective(sentences: List[str], max_results: int = 3) -> List[str]:
    """Extrai as frases que descrevem o objetivo do artigo."""
    matches = _find_matches(sentences, _OBJECTIVE_PATTERNS, max_results)
    if not matches:
        matches = _find_matches(sentences, _OBJECTIVE_PATTERNS_BROAD, max_results)
    return matches


def extract_problem(sentences: List[str], max_results: int = 3) -> List[str]:
    """Extrai as frases que descrevem o problema abordado pelo artigo."""
    matches: List[str] = []
    for sent in sentences:
        if _PROBLEM_PRIMARY_RE.search(sent) or _PROBLEM_SECONDARY_RE.search(sent):
            if sent not in matches:
                matches.append(sent)
        if len(matches) >= max_results:
            break
    return matches


def extract_methodology(sentences: List[str], max_results: int = 3) -> List[str]:
    """Extrai as frases que descrevem a metodologia utilizada no artigo."""
    return _find_matches(sentences, _METHODOLOGY_PATTERNS, max_results)


def extract_contributions(sentences: List[str], exclude: Optional[List[str]] = None, max_results: int = 3) -> List[str]:
    """Extrai as frases de contribuicao do artigo, excluindo as ja usadas como objetivo."""
    exclude_set = set(exclude or [])

    def _collect(patterns: List[re.Pattern]) -> List[str]:
        found: List[str] = []
        for sent in sentences:
            if sent in exclude_set or _CREDIT_BOILERPLATE_RE.search(sent):
                continue
            if any(p.search(sent) for p in patterns) and sent not in found:
                found.append(sent)
            if len(found) >= max_results:
                break
        return found

    matches = _collect([_CONTRIBUTION_RE])
    if not matches:
        matches = _collect(_CONTRIBUTION_PATTERNS_BROAD)
    return matches


def extract_future_work(sentences: List[str], max_results: int = 3) -> List[str]:
    """Extrai as frases que mencionam trabalhos futuros, normalmente na conclusao."""
    return _find_matches(sentences, _FUTURE_WORK_PATTERNS, max_results)


def extract_info(paper: Dict) -> Dict[str, List[str]]:
    """Extrai objetivo, problema, metodologia, contribuicoes e trabalhos futuros de um artigo."""
    intro_zone = (paper.get("abstract", "") + " " + paper.get("intro_text", "")).strip()
    intro_sentences = split_sentences(intro_zone)
    body_sentences = split_sentences(paper.get("body_text", ""))
    conclusion_sentences = split_sentences(paper.get("conclusion_text", ""))

    objective = extract_objective(intro_sentences)
    if not objective:
        objective = extract_objective(body_sentences)

    problem = extract_problem(intro_sentences)
    if not problem:
        problem = extract_problem(body_sentences)

    methodology = extract_methodology(body_sentences)
    contributions = extract_contributions(body_sentences, exclude=objective)
    future_work = extract_future_work(conclusion_sentences)

    return {
        "objective": objective,
        "problem": problem,
        "methodology": methodology,
        "contributions": contributions,
        "future_work": future_work,
    }


def extract_corpus(categorized_corpus: Dict[str, Dict]) -> Dict[str, Dict]:
    """Aplica ``extract_info`` a todos os artigos categorizados do corpus."""
    result: Dict[str, Dict] = {}
    for name, paper in categorized_corpus.items():
        result[name] = extract_info(paper)
    return result


def extraction_brief(filename: str, info: Dict[str, List[str]]) -> str:
    """Monta um resumo textual com os trechos extraidos de um artigo."""
    lines = [f"Arquivo : {filename}"]
    for field, label in [
        ("objective", "Objetivo"),
        ("problem", "Problema"),
        ("methodology", "Metodologia"),
        ("contributions", "Contribuicoes"),
        ("future_work", "Trabalhos futuros"),
    ]:
        values = info.get(field, [])
        if not values:
            lines.append(f"  {label}: (não encontrado)")
        else:
            for i, v in enumerate(values, 1):
                snippet = v if len(v) <= 140 else v[:140] + "..."
                lines.append(f"  {label} [{i}]: {snippet}")
    return "\n".join(lines)
