"""Segmentacao de cada artigo em titulo, autores, secoes e referencias (Etapa 1).

Os PDFs cientificos nao trazem nenhuma marcacao estrutural explicita depois
da extracao de texto: tudo vira uma sequencia de linhas. Este modulo usa
heuristicas baseadas em expressoes regulares para reconstruir a estrutura
logica do artigo (titulo, autores, abstract, keywords, introducao, corpo,
conclusao e referencias bibliograficas), o que e o ponto de partida para as
etapas seguintes do pipeline (pre-processamento, extracao de informacao e
exportacao da ontologia).
"""

import re
from typing import Dict, List, Optional, Tuple

from .text_cleaning import clear_text

_ABSTRACT_RE = re.compile(r"^abstract\b|^a\s*b\s*s\s*t\s*r\s*a\s*c\s*t\s*$", re.I)
_KEYWORDS_RE = re.compile(r"^(?:keywords?|key\s*words?|index\s*terms?)\b", re.I)
_INTRODUCTION_RE = re.compile(r"^(?:\d+\.?\s*|[ivx]+[\.\)]\s*)?introduction\s*$", re.I)
_REFERENCES_RE = re.compile(r"^(?:\d+\.?\s*)?references?\s*$|^bibliography\s*$", re.I)

# Cabecalho numerado de secao, no formato "N. Titulo Curto" (sem ":" ou
# digitos no titulo, e no maximo seis palavras, para nao confundir com itens
# de lista numerada dentro do texto).
_NUMBERED_HEADER_RE = re.compile(r"^(\d+)\.?\s*([A-Z][^:(]{0,60})$")

_CONCLUSION_KEYWORDS_RE = re.compile(r"conclu|summary|final\s+remark|future", re.I)


def _is_top_level_header(line: str) -> Optional[Tuple[int, str]]:
    """Identifica se a linha e um cabecalho de secao numerado (ex.: "3. Methodology")."""
    s = line.strip()
    m = _NUMBERED_HEADER_RE.match(s)
    if not m:
        return None
    title = m.group(2).strip()
    if re.search(r"\d", title):
        return None
    if len(title.split()) > 6:
        return None
    return int(m.group(1)), title


def _fix_embedded_section_labels(text: str) -> str:
    """Corrige rotulos de secao (abstract, references) colados a outras linhas.

    Esse padrao e comum em PDFs de layout em duas colunas do ScienceDirect,
    onde a extracao de texto junta o rotulo de uma secao ao final da ultima
    linha do paragrafo anterior.
    """
    # "abstract" colado ao final de uma linha
    text = re.sub(r"([a-zA-Z])(abstract)\s*\n", r"\1\n\2\n", text, flags=re.I)
    text = re.sub(r"([a-zA-Z])(abstract)\s*$", r"\1\n\2", text, flags=re.I | re.MULTILINE)

    # "a b s t r a c t" (com espacos entre letras) colado ao final de uma linha
    spaced_abstract = r"[ \t]+a\s*b\s*s\s*t\s*r\s*a\s*c\s*t"
    text = re.sub(spaced_abstract + r"\s*\n", "\nabstract\n", text, flags=re.I)
    text = re.sub(spaced_abstract + r"\s*$", "\nabstract", text, flags=re.I | re.MULTILINE)

    # "REFERENCES" colado ao final de uma frase em minusculas
    text = re.sub(r"([a-z.,;:])\s*(REFERENCES?)\s*\n", r"\1\n\2\n", text)
    text = re.sub(r"([a-z.,;:])\s*(REFERENCES?)\s*$", r"\1\n\2", text, flags=re.MULTILINE)

    # Ligaduras de siglas quebradas pela extracao do PyPDF2 (ex.: "Iaa S" -> "IaaS")
    for bad, good in [
        ("Iaa S", "IaaS"), ("Paa S", "PaaS"),
        ("Saa S", "SaaS"), ("Daa S", "DaaS"),
        ("Faa S", "FaaS"), ("DDo S", "DDoS"),
        ("Io T", "IoT"),
    ]:
        text = text.replace(bad, good)

    # Remove ruido residual do bloco "article info / Article history"
    text = re.sub(r"\barticle\s+info\b", "", text, flags=re.I)
    text = re.sub(r"\bArticle\s+history\s*:?\b", "", text, flags=re.I)

    # Remove o nome do periodico quando colado ao inicio do titulo do artigo
    text = re.sub(
        r"^\s*Computers\s*&\s*Security(?:\s+TC\s+\d+\s+Brie[a-z]*\s+Papers)?\s+",
        "", text, flags=re.I | re.MULTILINE,
    )

    return text


# Palavras que indicam que a linha e informacao institucional (afiliacao),
# e nao parte do titulo ou da lista de autores.
_PAT_ORG = re.compile(
    r"(@|universi\w*|institut\w*|department|school|faculty|"
    r"laboratory|laboratoire|laborat[oó]rio|lab\b|college|center|centre|"
    r"ecole|école|facultad|departamento|"
    r"inc\.|ltd\.|^\d+\s+\w|\{.*\}|©|\bDOI\b|\bISSN\b|\bvol\b|\bpp\b)",
    re.I,
)

# Palavras de conexao comuns em nomes de pessoas (preposicoes, artigos etc.)
_NAME_CONNECTORS = {
    "de", "da", "do", "das", "dos", "of", "the", "and",
    "van", "der", "den", "la", "le", "les", "du", "el", "di",
    "für", "und", "aus",
}


def _is_name_like(segment: str) -> bool:
    """Heuristica que verifica se um segmento de texto parece um nome de pessoa."""
    seg = segment.strip().strip("*†‡§¶")
    if not seg:
        return False
    words = seg.split()
    if not (1 <= len(words) <= 4):
        return False
    for w in words:
        wl = w.lower().strip(".,")
        if wl in _NAME_CONNECTORS:
            continue
        if len(wl) == 1:
            continue
        if not w[0].isupper():
            return False
    return True


# Marcador de afiliacao em sobrescrito colado ao inicio de uma linha de afiliacao
_AFFIL_LEADING_MARKER_RE = re.compile(r"^([a-z0-9]{1,2})(?=[A-Z])")


def _strip_glued_affiliation_marker(name: str, known_markers: set) -> str:
    """Remove uma unica letra/digito de marcador de afiliacao colado ao fim do nome."""
    if not known_markers or len(name) < 2:
        return name
    marker = name[-1]
    if not marker.isalnum() or marker not in known_markers:
        return name
    base = name[:-1]
    if not base or not base[-1].isalpha():
        return name
    last_word_match = re.search(r"(\S+)$", base)
    if not last_word_match or not last_word_match.group(1)[0].isupper():
        return name
    return base


def _extract_title_authors(pre_lines: List[str]) -> Tuple[str, List[str], int]:
    """Extrai o titulo e a lista de autores do bloco de linhas antes do abstract."""
    lines = [l.strip() for l in pre_lines if l.strip()]

    title_lines: List[str] = []
    authors_lines: List[str] = []
    known_markers: set = set()
    state = "title"
    consumed = len(lines)

    for idx, line in enumerate(lines):
        if _PAT_ORG.search(line):
            marker_match = _AFFIL_LEADING_MARKER_RE.match(line)
            if marker_match:
                known_markers.add(marker_match.group(1))
            if state == "title":
                continue
            state = "affiliations"
            consumed = idx + 1
            continue

        if state == "affiliations":
            consumed = idx
            break

        segments = [s for s in line.split(",") if s.strip("*†‡§¶ \t") != ""]
        all_name_like = bool(segments) and all(_is_name_like(s) for s in segments)
        has_comma = "," in line
        has_and_names = bool(re.search(r"[A-Z][a-zA-Z'\-]+\s+and\s+[A-Z][a-zA-Z'\-]+", line))

        if state == "title":
            # Muda para o estado "authors" ao encontrar virgula ou "and" ligando nomes
            if title_lines and all_name_like and (has_comma or has_and_names):
                state = "authors"
                authors_lines.append(line)
            else:
                title_lines.append(line)
        elif state == "authors":
            if all_name_like or has_and_names:
                authors_lines.append(line)
            else:
                consumed = idx
                break

    title = " ".join(title_lines).strip()
    title = re.sub(r"[\*†‡§¶\s]+$", "", title)
    title = re.sub(r"\s*\d+\s*$", "", title).strip()
    if title and title[0].islower():
        title = title[0].upper() + title[1:]

    raw_authors = " ".join(authors_lines)
    raw_authors = re.sub(r"\band\b", ",", raw_authors, flags=re.I)
    authors: List[str] = []
    for a in raw_authors.split(","):
        a = a.strip().strip("*†‡§¶").rstrip("0123456789,;.").strip()
        a = re.sub(r"\s+[a-z]$", "", a).strip()  # remove marcador de afiliacao residual
        a = _strip_glued_affiliation_marker(a, known_markers)
        if a and 2 < len(a) < 60:
            authors.append(a)

    return title, authors, consumed


def _strip_label(line: str, label_re: re.Pattern) -> str:
    """Remove o rotulo de cabecalho (ex.: "Abstract:") e retorna o restante da linha."""
    s = line.strip()
    m = label_re.match(s)
    if not m:
        return s
    rest = s[m.end():]
    return rest.lstrip(" :\u2013\u2014-\t").strip()


def _extract_keywords(keywords_text: str) -> List[str]:
    """Extrai a lista de palavras-chave a partir do bloco de texto da secao Keywords."""
    text = keywords_text.strip()
    if not text:
        return []

    # Remove "abstract" colado ao final (comum em layout de duas colunas)
    text = re.sub(r"abstract\s*$", "", text, flags=re.I).strip()

    if re.search(r"[;•·|]", text):
        parts = re.split(r"[;•·|]", text)
    elif text.count(",") >= 2 and len(text) < 200:
        parts = re.split(r",", text)
    else:
        # Sem separador explicito: tenta detectar limites de palavra por
        # mudanca de capitalizacao (CamelCase / ACRONIMOS colados)
        parts = []
        for line in text.split("\n"):
            line = line.strip()
            if not line:
                continue
            sub = re.sub(r"([a-z])([A-Z]{2,})", r"\1\n\2", line)  # palavra + ACRONIMO
            sub = re.sub(r"([A-Z]{2,})([A-Z][a-z])", r"\1\n\2", sub)  # ACRONIMO + Palavra
            sub = re.sub(r"([a-z])([A-Z][a-z])", r"\1\n\2", sub)  # Palavra + Palavra
            parts.extend(sub.split("\n"))

    keywords = [k.strip().strip(".,;") for k in parts if k.strip()]
    keywords = [k for k in keywords if 0 < len(k) < 80]
    return keywords


_REF_BEGIN = [
    re.compile(r"^\s*\[\d+\]"),
    re.compile(r"^\s*\d{1,3}\.\s+[A-Z]"),
    re.compile(r"^[A-Z][a-zA-Z'\-]+(?:\s+[A-Z]{1,3})+[,\.]"),
    re.compile(r"^[A-Z][a-zA-Z'\-]+,\s+[A-Z]\.(?:\s?[A-Z]\.)?,"),
    re.compile(r"^[A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+){1,5},\s*(?:http|www)", re.I),
]
_REF_BOUNDARY_RE = re.compile(r"(?<=[.\]])\s*(?=[A-Z][a-zA-Z'\-]+\s+[A-Z]{1,3}\.?\s*,)")
_AUTHOR_BIO_RE = re.compile(r"^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\s+(?:is|received|obtained|has|was)\b", re.I)


def _extract_references_dense(refs_text: str) -> List[str]:
    """Extrai referencias de listas sem linha em branco entre as entradas.

    Usado como alternativa quando ``_extract_references`` encontra poucas
    referencias em um bloco de texto longo, o que indica que a lista esta
    densa (todas as referencias coladas em um unico paragrafo).
    """
    blob = re.sub(r"\s+", " ", refs_text).strip()
    blob = re.sub(r"^references?\s*", "", blob, flags=re.I)

    parts = _REF_BOUNDARY_RE.split(blob)
    return [p.strip() for p in parts if len(p.strip()) > 15]


def _extract_references(refs_text: str) -> List[str]:
    """Extrai a lista de referencias bibliograficas do bloco de texto da secao References."""
    text = re.sub(r"^references?\s*\n|^bibliography\s*\n", "", refs_text, flags=re.I | re.M)

    lines = text.split("\n")
    references: List[str] = []
    current: List[str] = []
    in_bio = False

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if current and not in_bio:
                references.append(" ".join(current).strip())
            current = []
            in_bio = False
            continue

        if _AUTHOR_BIO_RE.match(stripped):
            # Inicio de uma biografia de autor (comum apos as referencias);
            # essas linhas sao descartadas, nao fazem parte da bibliografia.
            if current and not in_bio:
                references.append(" ".join(current).strip())
            current = []
            in_bio = True
            continue

        if in_bio:
            continue

        is_new_ref = any(pat.match(stripped) for pat in _REF_BEGIN)
        if is_new_ref:
            if current:
                references.append(" ".join(current).strip())
            current = [stripped]
        else:
            current.append(stripped) if current else current.extend([stripped])

    if current and not in_bio:
        references.append(" ".join(current).strip())

    return [r for r in references if len(r) > 15]


_JOURNAL_HEADER_RE = re.compile(r"([A-Za-z][A-Za-z &]{2,40}?)\s+(\d{1,4})\s*\(\s*(\d{4})\s*\)\s*\d")
_DOI_RE = re.compile(r"10\.\d{4,9}/[^\s,)]+")


def _extract_metadata(raw_text: str) -> Dict[str, str]:
    """Extrai metadados do artigo (journal, ano e DOI) a partir do inicio do texto bruto."""
    metadata: Dict[str, str] = {}
    zone = raw_text[:4000]

    m = _JOURNAL_HEADER_RE.search(zone)
    if m:
        metadata["journal"] = re.sub(r"\s+", " ", m.group(1)).strip()
        metadata["year"] = m.group(3)

    doi = _DOI_RE.search(raw_text[:5000])
    if doi:
        metadata["doi"] = doi.group(0).rstrip(".,;)")

    return metadata


def categorize_paper(paper_key: str, raw_text: str) -> Dict:
    """Segmenta o texto bruto de um artigo em titulo, autores e secoes principais."""
    metadata = _extract_metadata(raw_text)
    metadata["filename"] = paper_key

    text = clear_text(raw_text)
    text = _fix_embedded_section_labels(text)
    lines = text.split("\n")
    n = len(lines)

    # Localiza os cabecalhos de Abstract e Keywords
    abstract_idx: Optional[int] = None
    keywords_idx: Optional[int] = None
    for i, line in enumerate(lines):
        s = line.strip()
        if abstract_idx is None and _ABSTRACT_RE.match(s):
            abstract_idx = i
        if keywords_idx is None and _KEYWORDS_RE.match(s):
            keywords_idx = i
        if abstract_idx is not None and keywords_idx is not None:
            break

    search_start = max(
        (abstract_idx if abstract_idx is not None else -1),
        (keywords_idx if keywords_idx is not None else -1),
        -1,
    ) + 1

    # Localiza o cabecalho de Referencias
    refs_idx = n
    for i in range(search_start, n):
        if _REFERENCES_RE.match(lines[i].strip()):
            refs_idx = i
            break

    # Localiza o cabecalho de Introducao (explicito ou pelo primeiro cabecalho numerado)
    intro_idx: Optional[int] = None
    for i in range(search_start, refs_idx):
        if _INTRODUCTION_RE.match(lines[i].strip()):
            intro_idx = i
            break
    if intro_idx is None:
        for i in range(search_start, refs_idx):
            if _is_top_level_header(lines[i]):
                intro_idx = i
                break
    if intro_idx is None:
        intro_idx = min(search_start, refs_idx)

    # Localiza todos os cabecalhos de secao entre Introducao e Referencias
    header_positions: List[int] = []
    for i in range(intro_idx + 1, refs_idx):
        if _is_top_level_header(lines[i]):
            header_positions.append(i)

    intro_end = header_positions[0] if header_positions else refs_idx

    # Localiza o inicio da secao de Conclusao
    conclusion_idx: Optional[int] = None
    for i in reversed(header_positions):
        _, title_h = _is_top_level_header(lines[i])
        if _CONCLUSION_KEYWORDS_RE.search(title_h):
            conclusion_idx = i
            break
    if conclusion_idx is None and header_positions:
        conclusion_idx = header_positions[-1]
    if conclusion_idx is None:
        conclusion_idx = refs_idx

    # Monta os marcadores de inicio de Abstract, Keywords e Introducao, em ordem
    markers: List[Tuple[int, str]] = []
    if abstract_idx is not None:
        markers.append((abstract_idx, "abstract"))
    if keywords_idx is not None:
        markers.append((keywords_idx, "keywords"))
    markers.append((intro_idx, "introduction"))
    markers.sort()

    spans: Dict[str, Tuple[int, int]] = {}
    for idx, (pos, label) in enumerate(markers):
        end = markers[idx + 1][0] if idx + 1 < len(markers) else refs_idx
        spans[label] = (pos, end)

    pre_lines = lines[: markers[0][0]]

    def zone_text(label: str, header_re: re.Pattern) -> str:
        """Extrai o conteudo de uma das zonas marcadas (abstract ou keywords)."""
        if label not in spans:
            return ""
        pos, end = spans[label]
        inline = _strip_label(lines[pos], header_re)
        rest = "\n".join(lines[pos + 1: end]).strip()
        return (inline + "\n" + rest).strip() if inline else rest

    abstract_text = zone_text("abstract", _ABSTRACT_RE)
    keywords_raw = zone_text("keywords", _KEYWORDS_RE)
    keywords = _extract_keywords(keywords_raw)

    intro_text = "\n".join(lines[intro_idx:intro_end]).strip()
    middle_text = "\n".join(lines[intro_end:conclusion_idx]).strip()
    conclusion_text = "\n".join(lines[conclusion_idx:refs_idx]).strip()
    refs_text = "\n".join(lines[refs_idx:]).strip()

    title, authors, consumed = _extract_title_authors(pre_lines)

    # Trata artigos sem cabecalho de Abstract explicito: usa o texto restante
    # antes do titulo/autores como abstract, se houver paragrafos longos.
    if abstract_idx is None:
        leftover = [l.strip() for l in pre_lines if l.strip()][consumed:]
        leftover_text = "\n".join(l for l in leftover if len(l) > 100)
        if leftover_text:
            abstract_text = leftover_text

    references = _extract_references(refs_text) if refs_text else []
    if refs_text and len(references) < 8 and len(refs_text) > 800:
        dense_references = _extract_references_dense(refs_text)
        if len(dense_references) > len(references):
            references = dense_references

    body_text = "\n\n".join(t for t in [intro_text, middle_text, conclusion_text] if t).strip()

    return {
        "filename": paper_key,
        "title": title,
        "authors": authors,
        "abstract": abstract_text,
        "keywords": keywords,
        "intro_text": intro_text,
        "conclusion_text": conclusion_text,
        "body_text": body_text,
        "references": references,
        "metadata": metadata,
    }


def categorize_corpus(corpus: Dict[str, str]) -> Dict[str, Dict]:
    """Aplica ``categorize_paper`` a todos os artigos do corpus.

    Se um artigo falhar a categorizacao, ele entra no resultado com os campos
    estruturais vazios (e o texto bruto preservado em ``body_text``), para
    que o restante do pipeline continue funcionando.
    """
    result = {}
    for name, text in corpus.items():
        print(f"  - Categorizando: {name}")
        try:
            result[name] = categorize_paper(name, text)
        except Exception as e:
            print(f"    X Erro ao categorizar '{name}': {e}")
            result[name] = {
                "filename": name,
                "title": "", "authors": [], "abstract": "", "keywords": [],
                "intro_text": "", "conclusion_text": "", "body_text": text,
                "references": [], "metadata": {},
            }
    return result


def paper_brief(paper: Dict) -> str:
    """Monta um resumo textual com as principais informacoes de um artigo categorizado."""
    return "\n".join([
        f"Arquivo     : {paper['filename']}",
        f"Titulo      : {paper['title'][:80]}{'...' if len(paper['title']) > 80 else ''}",
        f"Autores     : {', '.join(paper['authors'])}",
        f"Ano         : {paper['metadata'].get('year', '?')}",
        f"DOI         : {paper['metadata'].get('doi', '?')}",
        f"Journal     : {paper['metadata'].get('journal', '?')}",
        f"Abstract    : {len(paper['abstract'])} chars",
        f"Keywords    : {paper['keywords']}",
        f"Intro       : {len(paper['intro_text'])} chars",
        f"Conclusao   : {len(paper['conclusion_text'])} chars",
        f"Corpo total : {len(paper['body_text'])} chars",
        f"Refs        : {len(paper['references'])} referencias extraidas",
    ])
