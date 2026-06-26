"""Pre-processamento de texto em PLN: normalizacao, tokenizacao, remocao de
stop-words, lematizacao e stemming (Etapa 1).

O pipeline de pre-processamento e aplicado separadamente ao abstract, ao
corpo do texto e a cada secao adicional do artigo, e produz a lista final de
tokens que alimenta os modelos de linguagem (bag-of-words e n-gramas).
"""

import re
import unicodedata
from typing import Dict, List, Optional

import nltk
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer, SnowballStemmer, WordNetLemmatizer

for _resource in ["stopwords", "wordnet", "omw-1.4"]:
    try:
        nltk.data.find(f"corpora/{_resource}")
    except LookupError:
        nltk.download(_resource, quiet=True)

# Comprimento minimo de um token para ser considerado informacional
TOKEN_MIN_LEN = 3

_STOPWORDS_NLTK = set(stopwords.words("english"))

# Stop-words adicionais tipicas de artigos academicos (linguagem de
# articulacao do texto, nao relacionadas ao conteudo tecnico do artigo)
_STOPWORDS_ACADEMIC = {
    # Vocabulario estrutural do artigo
    "paper", "article", "study", "work", "research", "propose", "proposed",
    "present", "presented", "show", "shown", "figure", "fig", "table", "section",
    "et", "al", "also", "thus", "therefore", "however", "furthermore", "moreover",
    "hence", "whereas", "although", "despite", "due", "based", "using", "used",
    "use", "via", "respectively", "e.g", "i.e", "etc", "http", "www",
    # Numeros ordinais residuais que sobrevivem a tokenizacao
    "th", "st", "nd", "rd",
    # Conectivos e verbos genericos, pouco informativos para o corpus
    "make", "made", "made", "take", "taken", "give", "given", "get", "got",
    "become", "became", "provide", "provided", "consider", "considered",
    "evaluate", "evaluated", "analyze", "analyzed", "discuss", "discussed",
    "describe", "described", "focus", "focused", "achieve", "achieved",
    "require", "required", "need", "needed", "allow", "allowed", "able",
    "well", "high", "low", "large", "small", "new", "different", "various",
    "many", "several", "specific", "particular", "general", "important",
    "significant", "effective", "efficient", "main", "key",
    # Palavras de uma ou duas letras residuais de outros idiomas
    "le", "la", "el", "de", "du", "al",
}
_STOPWORDS = _STOPWORDS_NLTK | _STOPWORDS_ACADEMIC

_lemmatizer = WordNetLemmatizer()
_stemmer_porter = PorterStemmer()
_stemmer_snowball = SnowballStemmer("english")


def normalize(text: str) -> str:
    """Normaliza o texto: remove acentos, converte para minusculas e limpa ruido."""
    # Remove diacriticos (acentos) decompondo e descartando os combinantes
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))

    text = text.lower()

    text = re.sub(r"https?://\S+|www\.\S+", " ", text)  # URLs
    text = re.sub(r"\S+@\S+\.\S+", " ", text)  # e-mails

    # Citacoes no estilo numerico "[12]" e no estilo autor-data "(Silva et al., 2020)"
    text = re.sub(r"\[\d+(?:[,\s]\d+)*\]", " ", text)
    text = re.sub(r"\([A-Z][a-z]+(?:\s+et\s+al\.?)?,?\s*\d{4}\)", " ", text)

    # Numeros isolados e sequencias numericas (incluindo ordinais "1st", "2nd")
    text = re.sub(r"\b\d+(?:\.\d+)?(?:st|nd|rd|th)?\b", " ", text)

    # Remove pontuacao, preservando o hifen interno de palavras compostas
    text = re.sub(r"[^\w\s\-]", " ", text)
    text = re.sub(r"(?<!\w)-|-(?!\w)", " ", text)  # remove hifens isolados/nas bordas

    text = re.sub(r"\s+", " ", text)

    return text.strip()


def tokenize(text: str) -> List[str]:
    """Tokeniza o texto normalizado e descarta tokens menores que ``TOKEN_MIN_LEN``."""
    return [t for t in text.split() if len(t) >= TOKEN_MIN_LEN]


def remove_stopwords(tokens: List[str], extras_stopwords: Optional[set] = None) -> List[str]:
    """Remove stop-words (NLTK + academicas) da lista de tokens."""
    sw = _STOPWORDS.copy()
    if extras_stopwords:
        sw |= extras_stopwords

    return [t for t in tokens if t not in sw and len(t) >= TOKEN_MIN_LEN]


def _infer_pos(token: str) -> str:
    """Heuristica simples de classe gramatical para orientar o lematizador do WordNet."""
    if re.search(r"ing$", token) and len(token) > 5:
        return "v"
    if re.search(r"(?:ed|ate|ize|ise)$", token) and len(token) > 5:
        return "v"
    if re.search(r"(?:ful|ous|ive|ible|able|ic|ical|al)$", token):
        return "a"
    if re.search(r"ly$", token) and len(token) > 4:
        return "r"
    return "n"


def lemmatize(tokens: List[str]) -> List[str]:
    """Reduz cada token a sua forma lematizada (forma canonica de dicionario)."""
    return [_lemmatizer.lemmatize(t, pos=_infer_pos(t)) for t in tokens]


def stem(tokens: List[str], algorithm: str = "snowball") -> List[str]:
    """Reduz cada token a seu radical (stemming), via Porter ou Snowball."""
    stemmer = _stemmer_snowball if algorithm == "snowball" else _stemmer_porter
    return [stemmer.stem(t) for t in tokens]


def preprocess(
    text: str,
    apply_lemmatizer: bool = True,
    apply_stemming: bool = False,
    extras_stopwords: Optional[set] = None,
) -> Dict:
    """Executa o pipeline completo de pre-processamento sobre um texto.

    Etapas: normalizacao -> tokenizacao -> remocao de stop-words ->
    lematizacao (opcional) -> stemming (opcional, aplicado apos a
    lematizacao quando ambos estao ativos).
    """
    text_norm = normalize(text)
    tokens = tokenize(text_norm)
    tokens = remove_stopwords(tokens, extras_stopwords)

    result = {
        "normalized_tokens": tokens,
        "lemmatized_tokens": [],
        "stemmed_tokens": [],
        "normalized_text": text_norm,
    }

    tokens_for_stem = tokens
    if apply_lemmatizer:
        tokens_lem = lemmatize(tokens)
        tokens_lem = remove_stopwords(tokens_lem, extras_stopwords)
        result["lemmatized_tokens"] = tokens_lem
        tokens_for_stem = tokens_lem

    if apply_stemming:
        result["stemmed_tokens"] = stem(tokens_for_stem)

    return result


def preprocess_paper(paper: Dict, apply_lemmatizer: bool = True, apply_stemming: bool = False) -> Dict:
    """Aplica o pre-processamento ao abstract, corpo e secoes de um artigo categorizado."""
    kwargs = dict(apply_lemmatizer=apply_lemmatizer, apply_stemming=apply_stemming)

    abstract_pp = preprocess(paper.get("abstract", ""), **kwargs)
    body_pp = preprocess(paper.get("body_text", ""), **kwargs)

    sections_pp = {}
    for sec_name, sec_text in paper.get("sections", {}).items():
        sections_pp[sec_name] = preprocess(sec_text, **kwargs)

    # Usa os tokens lematizados quando disponiveis; caso contrario, os normalizados
    total_tokens = (
        (abstract_pp["lemmatized_tokens"] or abstract_pp["normalized_tokens"])
        + (body_pp["lemmatized_tokens"] or body_pp["normalized_tokens"])
    )

    return {
        "filename": paper["filename"],
        "abstract_pp": abstract_pp,
        "body_pp": body_pp,
        "sections_pp": sections_pp,
        "total_tokens": total_tokens,
    }
