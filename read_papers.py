from pathlib import Path
from PyPDF2 import PdfReader
import concurrent.futures

def read_papers(path: str):
    folder_path = Path(path)
    paper_texts = dict()
    
    pdf_files = [f for f in folder_path.iterdir() if f.is_file() and f.name.endswith('.pdf')]

    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = executor.map(_read_single_paper, pdf_files)
        for file_name, text in results:
            paper_texts[file_name] = text

    return paper_texts

def _read_single_paper(file_path: Path):
    print(f'Lendo artigo: "{file_path.name}"')
    reader = PdfReader(file_path)

    pages = [page.extract_text() for page in reader.pages if page.extract_text()]
    full_text = "\n".join(pages)
    
    return file_path.name, full_text