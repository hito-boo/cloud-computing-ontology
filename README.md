# Ontologia de Artigos Científicos - Cloud Computing & Segurança

Trabalho de Inteligência Artificial (Processamento de Linguagem Natural) da
Universidade Estadual de Maringá (UEM), Departamento de Informática. O
enunciado completo está em [`docs/2TrabalhoIIA-CC.AnaliseDeArtigosCientificos.Versao02.pdf`](docs/2TrabalhoIIA-CC.AnaliseDeArtigosCientificos.Versao02.pdf).

## Objetivo

Modelar uma ontologia sobre a estrutura de um artigo científico e implementar
um pipeline de PLN que, a partir de um córpus de PDFs, seja capaz de:

1. ler os PDFs e identificar título, autores, seções e referências de cada artigo;
2. pré-processar o texto e gerar modelos de linguagem (bag-of-words, n-gramas);
3. extrair objetivo, problema, metodologia e contribuições de cada artigo;
4. exportar o resultado como uma ontologia de artigo científico;
5. gerar visualizações analíticas do córpus.

O enunciado proíbe o uso de bibliotecas de aprendizado de máquina ou modelos
pré-treinados (scikit-learn, spaCy, Transformers, BERT, Word2Vec etc.). Por
isso, todo o pipeline é construído com expressões regulares, heurísticas de
texto e estatística simples de frequência - sem nenhum modelo treinado.

## Córpus analisado

Tema escolhido: **Computação na Nuvem**, base **ScienceDirect**.

| | |
|---|---|
| Artigos | 12 PDFs, em `data/Artigos/` |
| Periódico | *Computers & Security* (Elsevier) |
| Período | 2014 – 2024 |
| Assuntos | auditoria e integridade de dados na nuvem, criptografia baseada em atributos, detecção de intrusão em redes virtuais, forense digital, segurança em IoT, blockchain, computação móvel-nuvem, entre outros |

## Estrutura do projeto

```
main.py                       Ponto de entrada: executa as etapas em sequência
pipeline/                     Código-fonte de cada etapa do pipeline
    reading.py                    Leitura dos PDFs (PyPDF2)
    text_cleaning.py              Limpeza de artefatos de extração de PDF
    categorization.py             Segmentação do artigo em título/autores/seções
    preprocessing.py              Normalização, stop-words, lematização, stemming
    language_models.py            Bag-of-words, n-gramas, termos mais frequentes
    extraction.py                  Objetivo, problema, metodologia, contribuições
    ontology_export.py             Exportação da ontologia em JSON-LD
    visualization.py               Gráficos analíticos do córpus
scripts/
    download_nltk_resources.py    Utilitário opcional para baixar recursos do NLTK
data/Artigos/                  PDFs dos 12 artigos científicos analisados
docs/                           Enunciado original do trabalho
output/                         Gerado pela execução do pipeline (não versionado)
```

## Cobertura do enunciado

| Etapa do enunciado | Onde está implementada | Observações |
|---|---|---|
| 1 - Leitura de PDF, pré-processamento, modelos de linguagem, 10 termos mais citados, extração de referências | `pipeline/reading.py`, `text_cleaning.py`, `categorization.py`, `preprocessing.py`, `language_models.py` | Leitura em paralelo (ThreadPoolExecutor); stop-words removidas com NLTK + lista acadêmica própria; lematização via WordNet; stemming opcional (desligado por padrão) |
| 2 - Objetivo, problema, metodologia, contribuições | `pipeline/extraction.py` | Casamento de padrões regex sobre as frases do abstract/introdução, corpo e conclusão |
| 3 - Ontologia em arquivo (RDF/XML, Turtle, OWL, Frames ou JSON-LD) | `pipeline/ontology_export.py` | Formato escolhido: **JSON-LD**, com vocabulário `schema.org` para os campos bibliográficos e um vocabulário próprio (`concepts:`) para os campos extraídos na etapa 2 |
| Observações - visualizações (palavras mais citadas, nuvem de palavras, técnicas mais mencionadas, evolução temporal, trabalhos futuros) | `pipeline/visualization.py` | Implementadas 8 visualizações (ver tabela abaixo), cobrindo todos os itens pedidos e mais algumas complementares (coocorrência, similaridade entre artigos) |
| 4 - Avaliação de desempenho do sistema de extração | *não está no código* | Etapa de avaliação qualitativa/quantitativa a ser feita manualmente sobre `extraction_output.json`, para apresentação nos slides |
| 5 - Apresentação (slides) | *não está no código* | Entregável separado, fora do escopo deste repositório |

## Detalhamento das etapas

### Etapa 1 - Leitura, categorização e modelos de linguagem

- **`reading.py`** - lê todos os PDFs de `data/Artigos/` em paralelo
  (`ThreadPoolExecutor`) usando `PyPDF2`, concatenando o texto de todas as
  páginas de cada artigo.
- **`text_cleaning.py`** - remove ruído típico de PDFs de periódico
  (numeração de página, cabeçalho/rodapé do journal, DOI, copyright, datas de
  submissão), normaliza caracteres Unicode e reconecta palavras quebradas por
  hifenização no fim da linha.
- **`categorization.py`** - usa heurísticas de regex para reconstruir a
  estrutura lógica do artigo a partir do texto plano: título, autores,
  abstract, keywords, introdução, corpo, conclusão e lista de referências
  bibliográficas, além de metadados (ano, DOI, periódico).
- **`preprocessing.py`** - normaliza o texto (minúsculas, remoção de
  acentos, URLs, e-mails, citações `[12]`/`(Silva et al., 2020)`, números),
  tokeniza, remove stop-words (NLTK + lista própria de termos acadêmicos
  pouco informativos) e aplica lematização (WordNet) e, opcionalmente,
  stemming (Porter ou Snowball).
- **`language_models.py`** - constrói o modelo de **bag-of-words** e de
  **n-gramas** (bigramas e trigramas) de cada artigo e do córpus agregado, e
  identifica os termos mais frequentes (excluindo as referências
  bibliográficas, que ficam fora do `body_text` usado nesta etapa).

### Etapa 2 - Extração de informação

`extraction.py` divide o texto em frases (com tratamento de abreviações como
"et al.", "e.g." e iniciais de nomes) e procura, por casamento de padrões:

- **Objetivo** - frases como *"the objective/aim/goal of this paper is to..."*
  ou, na ausência destas, padrões mais amplos como *"in this paper, we propose..."*;
- **Problema** - frases que mencionam "problem" ou que combinam um desafio
  ("challenge", "issue", "gap", "limitation") com um verbo de enfrentamento
  ("address", "solve", "overcome", "tackle");
- **Metodologia** - frases com termos como "method", "approach", "framework",
  "dataset", ou que descrevem entrevistas/surveys/experimentos conduzidos;
- **Contribuições** - frases com "contributes to" ou, como alternativa,
  "the main/key contributions of this paper", excluindo as frases já usadas
  como Objetivo;
- **Trabalhos futuros** - frases na conclusão com "future work/research",
  "we plan to", "open problem/issue", entre outras.

### Etapa 3 - Ontologia do córpus em JSON-LD

`ontology_export.py` combina os dados da categorização (Etapa 1) com os da
extração (Etapa 2) em um documento JSON-LD:

- um nó `schema:ScholarlyArticle` por artigo, com `id` (URN estável derivado
  do nome do arquivo), título, autores, ano, DOI, periódico, abstract,
  keywords e referências mapeados para termos de `schema.org`;
- os campos extraídos na Etapa 2 (objetivo, problema, metodologia,
  contribuições, trabalhos futuros) mapeados para um vocabulário próprio
  (`concepts:hasObjective`, `concepts:hasProblem` etc.);
- um anexo `corpusTopTerms` com os unitermos/bigramas/trigramas mais
  frequentes do córpus, calculados na Etapa 1.

### Visualizações analíticas

`visualization.py` gera 8 gráficos, salvos em `output/visualizations/`:

| # | Arquivo | Visualização |
|---|---|---|
| 1 | `1_bar_top_terms.png` | Barras com os termos mais frequentes do córpus |
| 2 | `2_wordcloud_general.png` | Nuvem de palavras geral do córpus |
| 3 | `3_bar_techniques.png` | Técnicas de cloud/segurança mais mencionadas |
| 4 | `4_heatmap_temporal.png` | Evolução temporal dos termos mais frequentes, por ano |
| 5a/5b | `5a_bar_future_work.png` / `5b_wordcloud_future_work.png` | Termos mais frequentes nas frases de trabalhos futuros |
| 6 | `6_heatmap_cooccurrence.png` | Coocorrência entre os termos mais frequentes |
| 7a/7b | `7a_heatmap_similarity.png` / `7b_network_similarity.png` | Similaridade de Jaccard entre artigos (heatmap e diagrama de rede) |
| 8 | `8_word_tree_cloud.png` | Árvore de palavras com o contexto do termo "cloud" |

## Tecnologias utilizadas

| Biblioteca | Uso |
|---|---|
| Python 3 (stdlib: `re`, `json`, `collections`, `concurrent.futures`, `unicodedata`, `math`) | Lógica geral do pipeline |
| `PyPDF2` | Extração de texto dos PDFs |
| `nltk` | Stop-words, lematização (WordNet), stemming (Porter/Snowball) |
| `matplotlib` + `numpy` | Gráficos e heatmaps |
| `wordcloud` | Nuvens de palavras (opcional - se ausente, essas duas visualizações são puladas) |

Nenhuma biblioteca de aprendizado de máquina ou modelo pré-treinado é usada,
em conformidade com a restrição do enunciado.

## Como executar

```bash
pip install -r requirements.txt
python main.py
```

Na primeira execução, `pipeline/preprocessing.py` baixa automaticamente os
recursos do NLTK necessários (`stopwords`, `wordnet`, `omw-1.4`). Para
baixá-los manualmente com antecedência:

```bash
python scripts/download_nltk_resources.py
```

## Saídas geradas (em `output/`)

| Arquivo | Conteúdo |
|---|---|
| `categorized_output.json` | Estrutura completa de cada artigo: título, autores, abstract, keywords, seções, referências e metadados |
| `brief_output.txt` | Resumo legível por artigo (Etapa 1) |
| `top_terms_output.txt` | Ranking dos unitermos, bigramas e trigramas mais frequentes do córpus |
| `extraction_output.json` | Objetivo, problema, metodologia, contribuições e trabalhos futuros por artigo (Etapa 2) |
| `ontology_corpus.jsonld` | Ontologia final do córpus (Etapa 3) |
| `visualizations/*.png` | Os 8 gráficos analíticos |

## Exemplo de execução

Com os 12 artigos do córpus de referência, o pipeline extrai cerca de
**476 referências bibliográficas** no total e gera aproximadamente
**55.800 tokens** após o pré-processamento. Os unitermos mais frequentes do
córpus incluem termos como *data*, *cloud*, *security*, *user*, *access*,
*model* e *scheme*; entre os bigramas, destacam-se *data integrity* e
*cloud computing*. Os valores exatos podem variar de acordo com a versão do
NLTK/PyPDF2 instalada.

## Limitações conhecidas

- A segmentação do artigo (título, autores, seções) é feita por heurísticas
  de regex sobre o texto extraído do PDF; layouts muito diferentes do padrão
  Elsevier/ScienceDirect podem exigir ajustes nos padrões de
  `pipeline/categorization.py`.
- A extração de Objetivo/Problema/Metodologia/Contribuições (Etapa 2) é
  baseada em casamento de padrões linguísticos comuns em inglês acadêmico,
  não em compreensão semântica do texto; frases fora desses padrões podem não
  ser capturadas.
- A avaliação de desempenho do sistema de extração (Etapa 4 do enunciado) não
  está automatizada no código - deve ser feita manualmente, comparando
  `extraction_output.json` com uma leitura humana dos artigos, para compor a
  apresentação (Etapa 5).
