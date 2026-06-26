"""Limpeza de artefatos comuns na extracao de texto de PDFs cientificos.

O texto que sai do leitor de PDF traz ruido tipico de paginas de periodicos:
numeracao de pagina, cabecalhos/rodapes do journal, metadados editoriais
(DOI, copyright, datas de submissao) e palavras quebradas por hifenizacao no
fim da linha. As funcoes deste modulo normalizam o texto antes que ele siga
para as etapas de categorizacao e pre-processamento.
"""

import re
import unicodedata


def clear_text(raw_text: str) -> str:
    """Aplica toda a limpeza de artefatos sobre o texto bruto de um artigo."""
    text = _normalize_unicode(raw_text)
    text = _reconnect_hyphenated_words(text)

    lines = text.split("\n")
    lines = _remove_page_artifacts(lines)

    clean_text = "\n".join(lines)
    clean_text = re.sub(r"\n{3,}", "\n\n", clean_text)
    clean_text = re.sub(r"[ \t]{2,}", " ", clean_text)

    return clean_text.strip()


def _normalize_unicode(text: str) -> str:
    """Converte caracteres Unicode especiais (aspas, travessoes, ligaduras) para ASCII equivalente."""
    text = unicodedata.normalize("NFC", text)
    text = re.sub(r"[\u2010-\u2015\u2212]", "-", text)
    text = re.sub(r"[\u2018\u2019\u201A\u201B]", "'", text)
    text = re.sub(r"[\u201C\u201D\u201E\u201F]", '"', text)
    text = re.sub(r"\u2026", "...", text)
    text = re.sub(r"[\u2217\u2731]", "*", text)
    text = (
        text.replace("\ufb00", "ff")
        .replace("\ufb01", "fi")
        .replace("\ufb02", "fl")
        .replace("\ufb03", "ffi")
        .replace("\ufb04", "ffl")
    )
    return text


def _reconnect_hyphenated_words(text: str) -> str:
    """Reconecta palavras hifenizadas no fim da linha (quebra de PDF)."""
    return re.sub(r"-\s*\n\s*([a-záéíóúàèìòùâêîôûãõäëïöüç]+)", r"\1", text)


def _remove_page_artifacts(lines: list) -> list:
    """Remove linhas inteiras que sao artefatos de paginacao/cabecalho/rodape."""
    artifacts = [
        # Numeracao de pagina, em diferentes formatos
        re.compile(r"^\s*\d+\s*$"),
        re.compile(r"^\s*-\s*\d+\s*-\s*$"),
        re.compile(r"^\s*page\s+\d+\s*(?:of\s+\d+)?\s*$", re.I),
        re.compile(r"^[\s\-_=*#]{3,}\s*$"),
        # Cabecalhos e rodapes de periodico (ex.: "Computers & Security 45 (2014) 1-12")
        re.compile(r"^\s*\S[\w\s&,\-]+\d+\s*\(\d{4}\)\s*\d+\s*[\-eE]\s*\d+\s*$"),
        re.compile(r"^\s*[A-Za-z][A-Za-z &]{2,40}\d{1,4}\s*\(\d{4}\)\s*\d{4,7}\b"),
        re.compile(r"^\s*ScienceDirect\s*$", re.I),
        re.compile(r"^\s*Contents\s+lists\s+available\s+at\s+ScienceDirect", re.I),
        re.compile(r"^\s*journal\s+homepage\s*:", re.I),
        re.compile(r"^\s*j\s*o\s*u\s*r\s*n\s*a\s*l\s*h\s*o\s*m\s*e\s*p\s*a\s*g\s*e", re.I),
        re.compile(r"^\s*a\s*r\s*t\s*i\s*c\s*l\s*e\s+(?:i\s*n\s*f\s*o|h\s*i\s*s\s*t\s*o\s*r\s*y)\b", re.I),
        re.compile(r"^\s*www\.", re.I),
        re.compile(r"^\s*https?://", re.I),
        # Metadados editoriais (datas de submissao, copyright, DOI, licenca)
        re.compile(r"^\s*(?:received|revised|accepted|available\s+online|published)", re.I),
        re.compile(r"^\s*article\s+(?:info|history|type)\s*:?\s*$", re.I),
        re.compile(r"^\s*(?:[©®ª™]|\(c\))\s*\d{4}", re.I),
        re.compile(r"^\s*\d{4}-\d{4}/\$", re.I),
        re.compile(r"^\s*\d{4}-\d{4}/"),
        re.compile(r"^\s*all rights reserved", re.I),
        re.compile(r"^\s*open access", re.I),
        re.compile(r"^\s*doi\s*:\s*10\.", re.I),
        re.compile(r"^\s*http://dx\.doi\.org/", re.I),
        # Rodapes da pagina de rosto (autor correspondente, e-mail, telefone)
        re.compile(r"^\s*\*\s*Corresponding\s+author", re.I),
        re.compile(r"^\s*E-?mail\s+address\s*:", re.I),
        re.compile(r"^\s*Tel\.?(?:/fax)?:", re.I),
        # Marcadores de lista isolados em uma linha propria
        re.compile(r"^\s*[•·∙▪▸▹►◆◇○●]\s*$"),
    ]
    return [line for line in lines if not any(pattern.match(line) for pattern in artifacts)]
