import re
import unicodedata
from typing import Dict, List, Optional

import nltk
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer, SnowballStemmer
from nltk.stem import WordNetLemmatizer

for resource in ["stopwords", "wordnet", "omw-1.4"]:
    try:
        nltk.data.find(f"corpora/{resource}")
    except LookupError:
        nltk.download(resource, quiet=True)

# Comprimento mínimo de token para ser considerado informacional
TOKEN_MIN_LEN = 3

_STOPWORDS_NLTK = set(stopwords.words("english"))
_STOPWORDS_ACADEMIC = {
    # Estruturais do artigo
    "paper", "article", "study", "work", "research", "propose", "proposed",
    "present", "presented", "show", "shown", "figure", "fig", "table", "section",
    "et", "al", "also", "thus", "therefore", "however", "furthermore", "moreover",
    "hence", "whereas", "although", "despite", "due", "based", "using", "used",
    "use", "via", "respectively", "e.g", "i.e", "etc", "http", "www",
    # Números e unidades isoladas que passam pela tokenização
    "th", "st", "nd", "rd",
    # Conectivos e verbos genéricos
    "make", "made", "made", "take", "taken", "give", "given", "get", "got",
    "become", "became", "provide", "provided", "consider", "considered",
    "evaluate", "evaluated", "analyze", "analyzed", "discuss", "discussed",
    "describe", "described", "focus", "focused", "achieve", "achieved",
    "require", "required", "need", "needed", "allow", "allowed", "able",
    "well", "high", "low", "large", "small", "new", "different", "various",
    "many", "several", "specific", "particular", "general", "important",
    "significant", "effective", "efficient", "main", "key",
    # Palavras de um ou dois caracteres residuais
    "le", "la", "el", "de", "du", "al",
}
_STOPWORDS = _STOPWORDS_NLTK | _STOPWORDS_ACADEMIC

_lemmatizer = WordNetLemmatizer()
_stemmer_porter = PorterStemmer()
_stemmer_snowball = SnowballStemmer("english")

# Realiza uma normalização básica do texto
def normalize(text: str) -> str:
    # Unicode e diacríticos
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))

    # Lowercase
    text = text.lower()

    # URLs
    text = re.sub(r"https?://\S+|www\.\S+", " ", text)

    # Emails
    text = re.sub(r"\S+@\S+\.\S+", " ", text)

    # DOIs e Referências Bibliográficas
    text = re.sub(r"\[\d+(?:[,\s]\d+)*\]", " ", text)
    text = re.sub(r"\([A-Z][a-z]+(?:\s+et\s+al\.?)?,?\s*\d{4}\)", " ", text)

    # Números isolados e sequências numéricas
    text = re.sub(r"\b\d+(?:\.\d+)?(?:st|nd|rd|th)?\b", " ", text)

    # Remove pontuação, mantendo hífen dentro de palavras compostas
    text = re.sub(r"[^\w\s\-]", " ", text)

    # Remove hífens isolados ou no início/fim do token
    text = re.sub(r"(?<!\w)-|-(?!\w)", " ", text)

    # Colapsa múltiplos espaços
    text = re.sub(r"\s+", " ", text)

    return text.strip()

# Realiza uma tokenização simples após a normallização
def tokenize(text: str) -> List[str]:
    return [t for t in text.split() if len(t) >= TOKEN_MIN_LEN]

# Remove stop-words da lista de tokens
def remove_stopwords(tokens: List[str], extras_stopwords: Optional[set] = None,) -> List[str]:
    sw = _STOPWORDS.copy()
    if extras_stopwords:
        sw |= extras_stopwords

    return [t for t in tokens if t not in sw and len(t) >= TOKEN_MIN_LEN]

# Heurística simples que tenta orientar o lematizador
def _infer_pos(token: str) -> str:
    if re.search(r"ing$", token) and len(token) > 5:
        return "v"
    if re.search(r"(?:ed|ate|ize|ise)$", token) and len(token) > 5:
        return "v"
    if re.search(r"(?:ful|ous|ive|ible|able|ic|ical|al)$", token):
        return "a"
    if re.search(r"ly$", token) and len(token) > 4:
        return "r"
    return "n"

# Realiza a lematização dos tokens
def lemmatize(tokens: List[str]) -> List[str]:
    return [_lemmatizer.lemmatize(t, pos=_infer_pos(t)) for t in tokens]

# Aplica stemming aos tokens
def stem(tokens: List[str], algorithm: str = "snowball") -> List[str]:
    stemmer = _stemmer_snowball if algorithm == "snowball" else _stemmer_porter
    return [stemmer.stem(t) for t in tokens]

# Realiza o pipeline de pré-processamento
def preprocess(text: str, apply_lemmatizer: bool = True, apply_stemming: bool = False, extras_stopwords: Optional[set] = None) -> Dict:
    # Normalização
    text_norm = normalize(text)

    # Tokenização
    tokens = tokenize(text_norm)

    # Remoção de stop-words
    tokens = remove_stopwords(tokens, extras_stopwords)

    result = {
        "normalized_tokens": tokens,
        "lemmatized_tokens": [],
        "stemmed_tokens": [],
        "normalized_text": text_norm,
    }

    # Lematização
    tokens_for_stem = tokens
    if apply_lemmatizer:
        tokens_lem = lemmatize(tokens)
        tokens_lem = remove_stopwords(tokens_lem, extras_stopwords)
        result["lemmatized_tokens"] = tokens_lem
        tokens_for_stem = tokens_lem

    # Etapa 5: stemming (opcional)
    if apply_stemming:
        result["stemmed_tokens"] = stem(tokens_for_stem)

    return result

# Função principal de pré-processamento para um artigo
def preprocess_paper(paper: Dict, apply_lemmatizer: bool = True, apply_stemming: bool = False) -> Dict:
    kwargs = dict(apply_lemmatizer=apply_lemmatizer, apply_stemming=apply_stemming)

    abstract_pp = preprocess(paper.get("abstract", ""), **kwargs)
    body_pp = preprocess(paper.get("body_text", ""), **kwargs)

    sections_pp = {}
    for sec_name, sec_text in paper.get("sections", {}).items():
        sections_pp[sec_name] = preprocess(sec_text, **kwargs)

    total_tokens = (abstract_pp["lemmatized_tokens"] or abstract_pp["normalized_tokens"]) + (body_pp["lemmatized_tokens"] or body_pp["normalized_tokens"])

    return {
        "filename": paper["filename"],
        "abstract_pp": abstract_pp,
        "body_pp": body_pp,
        "sections_pp": sections_pp,
        "total_tokens": total_tokens,
    }