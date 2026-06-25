import re
import unicodedata
from typing import List

def clear_text(raw_text: str) -> str:
    text = _normalize_unicode(raw_text)
    text = _correct_hyphen(text)

    lines = text.split("\n")
    lines = _remove_page_artifacts(lines)

    # Colapsar múltiplas linhas em branco em uma só
    clean_text = "\n".join(lines)
    clean_text = re.sub(r"\n{3,}", "\n\n", clean_text)

    # Remover espaços excessivos dentro de uma linha
    clean_text = re.sub(r"[ \t]{2,}", " ", clean_text)

    return clean_text.strip()

# Converter caracteres Unicode especiais para ASCII quando possível
def _normalize_unicode(text: str) -> str:
    text = unicodedata.normalize("NFC", text)
    text = re.sub(r"[\u2010-\u2015\u2212]", "-", text)
    text = re.sub(r"[\u2018\u2019\u201A\u201B]", "'", text)
    text = re.sub(r"[\u201C\u201D\u201E\u201F]", '"', text)
    text = re.sub(r"\u2026", "...", text)
    text = re.sub(r"[\u2217\u2731]", "*", text)
    text = (text.replace("\ufb00", "ff").replace("\ufb01", "fi")
                 .replace("\ufb02", "fl").replace("\ufb03", "ffi")
                 .replace("\ufb04", "ffl"))
    return text

# Reconectar palavras hifenizadas ao final da linha
def _correct_hyphen(text: str) -> str:
    return re.sub(r"-\s*\n\s*([a-záéíóúàèìòùâêîôûãõäëïöüç]+)", r"\1", text)

# Remover artefatos da página (numeração, cabeçalhos, caracteres especiais)
def _remove_page_artifacts(lines: List[str]) -> List[str]:
    artifacts = [
        # Paginação genérica
        re.compile(r"^\s*\d+\s*$"),
        re.compile(r"^\s*-\s*\d+\s*-\s*$"),
        re.compile(r"^\s*page\s+\d+\s*(?:of\s+\d+)?\s*$", re.I),
        re.compile(r"^[\s\-_=*#]{3,}\s*$"),

        # Cabeçalhos e Rodapés de journal
        re.compile(r"^\s*\S[\w\s&,\-]+\d+\s*\(\d{4}\)\s*\d+\s*[\-eE]\s*\d+\s*$"),
        re.compile(r"^\s*[A-Za-z][A-Za-z &]{2,40}\d{1,4}\s*\(\d{4}\)\s*\d{4,7}\b"),
        re.compile(r"^\s*ScienceDirect\s*$", re.I),
        re.compile(r"^\s*Contents\s+lists\s+available\s+at\s+ScienceDirect", re.I),
        re.compile(r"^\s*journal\s+homepage\s*:", re.I),
        re.compile(r"^\s*j\s*o\s*u\s*r\s*n\s*a\s*l\s*h\s*o\s*m\s*e\s*p\s*a\s*g\s*e", re.I),
        re.compile(r"^\s*a\s*r\s*t\s*i\s*c\s*l\s*e\s+(?:i\s*n\s*f\s*o|h\s*i\s*s\s*t\s*o\s*r\s*y)\b", re.I),
        re.compile(r"^\s*www\.", re.I),
        re.compile(r"^\s*https?://", re.I),

        # Metadados editoriais
        re.compile(r"^\s*(?:received|revised|accepted|available\s+online|published)", re.I),
        re.compile(r"^\s*article\s+(?:info|history|type)\s*:?\s*$", re.I),
        re.compile(r"^\s*(?:[©®ª™]|\(c\))\s*\d{4}", re.I),
        re.compile(r"^\s*\d{4}-\d{4}/\$", re.I),
        re.compile(r"^\s*\d{4}-\d{4}/"),
        re.compile(r"^\s*all rights reserved", re.I),
        re.compile(r"^\s*open access", re.I),
        re.compile(r"^\s*doi\s*:\s*10\.", re.I),
        re.compile(r"^\s*http://dx\.doi\.org/", re.I),

        # Rodapés de página de artigo
        re.compile(r"^\s*\*\s*Corresponding\s+author", re.I),
        re.compile(r"^\s*E-?mail\s+address\s*:", re.I),
        re.compile(r"^\s*Tel\.?(?:/fax)?:", re.I),

        # Outros - Marcadores isolados
        re.compile(r"^\s*[•·∙▪▸▹►◆◇○●]\s*$"),
    ]
    result = []
    for line in lines:
        if not any(pat.match(line) for pat in artifacts):
            result.append(line)
    return result