"""Pacote com as etapas do pipeline de PLN aplicado aos artigos do córpus.

Cada módulo corresponde a uma etapa do trabalho de IIA (Processamento de
Linguagem Natural) sobre Computação na Nuvem e Segurança:

    reading           -> leitura dos PDFs dos artigos (Etapa 1)
    text_cleaning     -> limpeza de artefatos de extração de PDF
    categorization    -> segmentação do artigo em titulo/autores/secoes (Etapa 1)
    preprocessing     -> normalizacao, tokenizacao, stop-words, lematizacao (Etapa 1)
    language_models   -> bag-of-words e n-gramas, termos mais frequentes (Etapa 1)
    extraction        -> objetivo, problema, metodologia e contribuicoes (Etapa 2)
    ontology_export   -> exportacao da ontologia do corpus em JSON-LD (Etapa 3)
    visualization     -> graficos e nuvens de palavras para analise do corpus

O orquestrador de todas as etapas fica em ``main.py``, na raiz do projeto.
"""
