"""Leitura dos artigos em PDF que compoem o corpus (Etapa 1).

Cada PDF da pasta de artigos e convertido em texto puro, concatenando o
conteudo de todas as paginas. A leitura de cada arquivo e independente, por
isso e feita em paralelo com um ``ThreadPoolExecutor`` para reduzir o tempo
total quando o corpus tem muitos artigos.
"""

import concurrent.futures
from pathlib import Path

from PyPDF2 import PdfReader


def read_papers(path: str) -> dict:
    """Le todos os PDFs de ``path`` e retorna ``{nome_do_arquivo: texto}``."""
    folder_path = Path(path)
    pdf_files = [f for f in folder_path.iterdir() if f.is_file() and f.name.endswith(".pdf")]

    paper_texts = {}
    with concurrent.futures.ThreadPoolExecutor() as executor:
        for file_name, text in executor.map(_read_single_paper, pdf_files):
            paper_texts[file_name] = text

    return paper_texts


def _read_single_paper(file_path: Path) -> tuple:
    """Extrai o texto de um unico PDF, pagina por pagina."""
    print(f'Lendo artigo: "{file_path.name}"')
    reader = PdfReader(file_path)

    pages = [page.extract_text() for page in reader.pages if page.extract_text()]
    full_text = "\n".join(pages)

    return file_path.name, full_text
