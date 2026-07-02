---
marp: true
theme: default
paginate: true
size: 16:9
---

<!--
Estes slides seguem a estrutura exigida pelo enunciado (Etapa 5) e incorporam
a Etapa 4 (avaliação de desempenho) dentro do item 7.
Marcadores 🔧 TODO indicam informação que o(a) autor(a) do trabalho precisa
preencher manualmente - não temos esse dado disponível.
Se a ferramenta de slides usada no VS Code não for o Marp, basta remover o
bloco de front-matter acima (entre as duas primeiras linhas "---"); a
separação dos slides pelas linhas "---" continua funcionando normalmente.
-->

# Ontologia de Artigos Científicos
## Cloud Computing

Universidade Estadual de Maringá - Departamento de Informática
Curso: Ciência da Computação
Disciplina: IIA - Introdução à Inteligência Artificial
Professor: Prof. Dr. Wagner Igarashi
Equipe: Caetano (RA: 135846), Lorenzo (RA 133076), Vitor da Rocha (RA 132769)

---

## Sumário

1. Introdução
2. Fundamentação teórica
3. Materiais e métodos
4. Fonte dos dados
5. Visualizações do córpus
6. Demonstração em artigos adicionais
7. Avaliação de desempenho do sistema
8. Conclusões
9. Bibliografia

---

# 1. Introdução

---

## O problema

- O volume de artigos científicos publicados cresce mais rápido do que a
  capacidade humana de lê-los e organizá-los manualmente.
- Ler, classificar e resumir manualmente um córpus de artigos é um processo
  lento e repetitivo.
- **Pergunta do trabalho:** é possível usar técnicas de PLN (sem modelos de
  aprendizado de máquina/pré-treinados) para extrair automaticamente a
  estrutura e o conteúdo essencial de um artigo científico?

---

## Modelagem do problema

Os artigos científicos foram modelados como uma **ontologia** com os seguintes
elementos, a serem extraídos automaticamente do PDF:

- Identificação: título, autores, ano, DOI, periódico
- Conteúdo: abstract, palavras-chave, introdução, corpo, conclusão
- Análise: objetivo, problema, metodologia, contribuições, trabalhos futuros
- Referências bibliográficas citadas

O código desenvolvido lê um diretório de PDFs e produz, para cada artigo,
uma instância estruturada dessa ontologia.

---

# 2. Fundamentação teórica

---

## Modelos de linguagem e pré-processamento

- **Tokenização**: quebra do texto em unidades (palavras/termos)
- **Stop-words**: remoção de palavras de alta frequência e baixo valor
  semântico (artigos, preposições, conectivos)
- **Lematização** (WordNet): reduz a palavra à sua forma canônica de
  dicionário (ex.: *"schemes" → "scheme"*)
- **Stemming** (Porter/Snowball): reduz a palavra ao seu radical, de forma
  mais agressiva que a lematização (disponível no código, desligado por
  padrão)
- **Bag-of-Words**: representa o texto pela contagem de frequência de cada
  termo, ignorando a ordem das palavras
- **N-gramas**: sequências de N termos consecutivos (bigramas, trigramas),
  úteis para capturar termos técnicos compostos (ex.: *"cloud computing"*)

---

## Extração de informação e ontologias

- **Extração de informação baseada em regras (rule-based IE)**: uso de
  expressões regulares e padrões linguísticos para localizar frases que
  expressam objetivo, problema, metodologia e contribuições.
- **Ontologias e Web Semântica**: estrutura formal de conceitos e relações de
  um domínio. Dentre os formatos possíveis (RDF/XML, Turtle, OWL, Frames,
  JSON-LD), o trabalho usa **JSON-LD**, que combina legibilidade com
  compatibilidade direta com APIs e o vocabulário padronizado do
  [schema.org](https://schema.org)

---

# 3. Materiais e métodos

---

## Linguagem e bibliotecas

| Biblioteca | Uso no projeto |
|---|---|
| Python 3 (stdlib) | Lógica geral do pipeline |
| `PyPDF2` | Extração de texto dos PDFs |
| `nltk` | Stop-words, lematização (WordNet), stemming |
| `matplotlib` + `numpy` | Gráficos e heatmaps |
| `wordcloud` | Nuvens de palavras |

Nenhuma biblioteca de aprendizado de máquina ou modelo pré-treinado foi
utilizada.

---

## Pipeline do sistema

```
PDFs (12 artigos)
   │
   ▼
1. Leitura (PyPDF2) ──► 2. Limpeza de artefatos de PDF
   │
   ▼
3. Categorização (regex) ──► título, autores, seções, referências
   │
   ▼
4. Pré-processamento ──► stop-words, lematização
   │
   ▼
5. Modelos de linguagem ──► bag-of-words, n-gramas, top termos
   │
   ▼
6. Extração de informação ──► objetivo, problema, metodologia, contribuições
   │
   ▼
7. Exportação da ontologia (JSON-LD) + Visualizações
```

---

# 4. Fonte dos dados

---

## Córpus analisado

- **Tema:** Cloud Computing (Computação em Nuvem)
- **Base:** ScienceDirect
- **Periódico de origem dos 12 artigos:** *Computers & Security* (Elsevier)
- **Período de publicação:** 2014 – 2024
- **Assuntos recorrentes:** auditoria e integridade de dados na nuvem,
  criptografia baseada em atributos, detecção de intrusão em redes virtuais,
  forense digital, segurança em IoT, computação móvel-nuvem

Termos de Busca: Cloud Computing
Article Type: Research Articles
Publication Title: Computers & Security
Subject Areas: Computer Science

---

## Os 12 artigos do córpus

| Título (resumido) | Ano | Refs. |
|---|---|---|
| SNAPS: snapshot based provenance system for VMs in the cloud | 2019 | 11 |
| Security analysis of a public auditing scheme for secure data storage | 2023 | 16 |
| Efficient security framework for detecting intrusions in virtual networks | 2019 | 35 |
| Trust or consequences? Causal effects of perceived risk... | 2017 | 53 |
| Self-Attention conditional GAN for... | 2024 | 32 |
| A survey of cloud computing data integrity schemes | 2017 | 96 |

---

## Os 12 artigos do córpus (continuação)

| Título (resumido) | Ano | Refs. |
|---|---|---|
| Sticky policies approach within cloud computing | 2017 | 41 |
| Optimized extreme learning machine for detecting DDoS attacks | 2021 | 32 |
| Cloud computing security: a survey of service-based models | 2022 | 58 |
| Parallel search over encrypted data under attribute-based encryption | 2015 | 22 |
| Achieving an effective, scalable and privacy-preserving data... | 2014 | 29 |
| A self-protecting agents based model for high-performance mobile-cloud | 2018 | 34 |

**Total: 12 artigos, 459 referências bibliográficas extraídas no total.**

---

# 5. Visualizações do córpus

---

## Palavras mais citadas nos artigos

![bg right:62% fit](output/visualizations/1_bar_top_terms.png)

Termos mais frequentes do córpus (unitermos, excluindo as referências):
**data** (1097), **cloud** (986), **user** (610), **scheme** (473),
**security** (469), **attack** (396), **model** (394)...

Bigrama mais citado: **"cloud compute"** (142) e **"data integrity"** (122).

---

## Nuvem de palavras geral

![bg right:65% fit](output/visualizations/2_wordcloud_general.png)

A nuvem reforça visualmente o predomínio dos termos relacionados a
armazenamento e proteção de dados em nuvem.

---

## Técnicas mais mencionadas nos artigos

![bg right:55% fit](output/visualizations/3_bar_techniques.png)

Reflete o foco do córpus em **integridade e confidencialidade de dados
armazenados na nuvem**.

---

## Evolução temporal dos termos

![bg right:55% fit](output/visualizations/4_heatmap_temporal.png)

- O heatmap mostra a frequência relativa (%) dos termos mais citados, ano a
  ano, permitindo observar a permanência de termos como *data* e *cloud*
  ao longo de toda a década analisada. Infelizmente poucos artigos estão sendo usados o que limita a visualização.

---

## Termos em trabalhos futuros

![bg right:55% fit](output/visualizations/5a_bar_future_work.png)

- A seção de trabalhos futuros foi identificada explicitamente em apenas
  **3 dos 12 artigos (25%)** - muitos artigos do córpus não têm uma
  subseção de "future work" claramente demarcada na conclusão

---

## Termos em trabalhos futuros

![bg right:55% fit](output/visualizations/5b_wordcloud_future_work.png)

---

## Visualizações complementares

Além do que foi pedido, foi gerado:

- **Heatmap de coocorrência**: quais termos aparecem próximos uns dos outros no texto
- **Similaridade entre artigos**: similaridade de Jaccard entre os conjuntos de termos de cada artigo, em heatmap e em diagrama de rede
- **Árvore de palavras**: contexto (palavras antes/depois) do termo "cloud" no córpus
---
## Visualizações complementares
- **Heatmap de coocorrência**
![bg right:60% fit](output/visualizations/6_heatmap_cooccurrence.png)
---
## Visualizações complementares
- **Similaridade entre artigos**
![bg right:60% fit](output/visualizations/7a_heatmap_similarity.png)
---
## Visualizações complementares
- **Similaridade entre artigos**
![bg right:60% fit](output/visualizations/7b_network_similarity.png)
---
## Visualizações complementares
- **Árvore de palavras**
![bg right:60% fit](output/visualizations/8_word_tree_cloud.png)
---

# 6. Demonstração prática em artigos adicionais

---

# Demonstração

  - A respeito da categorização estrutural, apenas o Ano de Publicação e o *Journal* não foram extraídos, além do DOI de um deles. Porém o restante foi encontrado. 
  - Enquanto em um dos artigos não foi achado os objetivos e as contribuições, o outro teve todos os dados inferidos.
  - É possível observar a importancia de frases padrões como: "the major contributions of this paper..." e "In future work...".

---

## Palavras mais citadas nos artigos de Demonstração

![bg right:62% fit](output_demonstracao/visualizations/1_bar_top_terms.png)


---

## Técnicas mais mencionadas nos artigos de Demonstração

![bg right:65% fit](output_demonstracao/visualizations/3_bar_techniques.png)

---

## Nuvem de palavras geral

![bg right:65% fit](output_demonstracao/visualizations/2_wordcloud_general.png)

---

# 7. Avaliação de desempenho do sistema

---

## Metodologia de avaliação

A avaliação foi feita em duas frentes:

1. **Quantitativa** - taxa de cobertura: em quantos artigos cada campo da
   ontologia foi efetivamente extraído (não vazio), calculada diretamente
   sobre as saídas reais do sistema (`categorized_output.json` e
   `extraction_output.json`) para os 12 artigos do córpus
2. **Qualitativa** - leitura manual de uma amostra das frases extraídas,
   comparando-as com o conteúdo real do artigo, para identificar acertos e
   limitações dos padrões de regex utilizados

---

## Resultado quantitativo - Etapa 1 (categorização)

| Campo | Cobertura |
|---|---|
| Título | 100% (12/12) |
| Autores | 100% (12/12) - média de 4,0 autores/artigo |
| Abstract | 100% (12/12) - média de 1.364 caracteres |
| Palavras-chave | 100% (12/12) - média de 5,4 termos/artigo |
| Ano de publicação | 100% (12/12) |
| DOI | 83% (10/12) |
| Referências bibliográficas | 100% (12/12) - 459 no total, média 38,2/artigo |


---

## Resultado quantitativo - Etapa 1 (categorização)

A categorização estrutural (campos bibliográficos) teve **desempenho muito
alto**, pois esses campos seguem um padrão visual/textual bastante regular
nos artigos da Elsevier/ScienceDirect.

---

## Resultado quantitativo - Etapa 2 (extração de informação)

| Campo | Cobertura | Méd. frases/artigo |
|---|---|---|
| Objetivo | 92% (11/12) | 1,2 |
| Problema | 100% (12/12) | 2,0 |
| Metodologia | 100% (12/12) | 3,0 |
| Contribuições | 50% (6/12) | 0,7 |
| Trabalhos futuros | 25% (3/12) | 0,2 |

**Apenas 2 dos 12 artigos (17%) tiveram os 5 campos extraídos
simultaneamente.**

---

## Exemplos de acerto

> **Objetivo** *(intrusion detection em redes virtuais)*:
> "In this paper, we propose a hypervisor level distributed network
> security (HLDNS) framework which is deployed on each processing server
> of cloud computing."

> **Trabalhos futuros** *(mesmo artigo)*:
> "Conclusions and future work - Network security is a major concern for
> wide adoption of the cloud computing."

Esses padrões ("in this paper, we propose...", "future work") são bastante
**convencionais na escrita acadêmica em inglês**, por isso o sistema os
reconhece com boa precisão.

---

## Exemplos de limitação

> **Problema** identificado *(artigo sobre auditoria de dados)*:
> "...to handle the problem of user revocation..., Wang et al. (2015)
> proposed a novel scheme, named Panda."

Esta frase descreve o problema resolvido por um **trabalho relacionado**
(Wang et al., 2015), não necessariamente o problema do próprio artigo -
um falso positivo típico de uma extração baseada apenas em palavras-chave
("problem"), sem compreensão de quem é o sujeito da frase.

- **Contribuições** (50% de cobertura) e **trabalhos futuros** (25%) tiveram
  desempenho mais baixo: a frase exata "contributes to" é rara, e nem todos
  os artigos têm uma subseção de "future work" explícita.

---

## Discussão dos resultados

- O sistema tem **alto desempenho em campos estruturais e bem padronizados**
  (título, autores, abstract, keywords, referências) - domínio onde regex
  sobre o layout do PDF funciona muito bem.
- O sistema tem **desempenho variável em campos semânticos livres**
  (objetivo, problema, metodologia, contribuições, trabalhos futuros) -
  domínio onde a linguagem natural tem muito mais variação, e uma
  abordagem por regras não consegue cobrir todos os estilos de escrita.
- Os padrões "amplos" (fallback) implementados em `extraction.py` aumentam a
  cobertura de Objetivo e Contribuições, mas podem reduzir a precisão em
  alguns casos (como no exemplo de falso positivo acima).

---

# 8. Conclusões

---

## Conclusões

- Foi possível modelar e implementar uma ontologia de artigo científico e um
  pipeline completo de PLN **sem o uso de modelos de aprendizado de
  máquina**, usando apenas pré-processamento clássico, modelos de linguagem
  estatísticos (BoW/n-gramas) e extração de informação baseada em regras.
- O sistema é **muito confiável para metadados estruturais** (título,
  autores, abstract, referências) e **parcialmente confiável para conteúdo
  semântico livre** (objetivo, problema, metodologia, contribuições,
  trabalhos futuros), com cobertura entre 25% e 100% dependendo do campo.

---

## Conclusões

- A ontologia em **JSON-LD** se mostrou um formato prático para representar
  os artigos de forma legível e interoperável com vocabulários da Web
  Semântica (`schema.org`).
- Limitações: dependência do layout do periódico de origem, e
  sensibilidade dos padrões de regex a formas alternativas de expressar a
  mesma ideia.


---

# 9. Bibliografia

---

## Bibliografia


- PyPDF2 - documentação oficial: https://pypdf2.readthedocs.io/
- NLTK - documentação oficial: https://www.nltk.org/
- Matplotlib - documentação oficial: https://matplotlib.org/
- WordCloud (Python) - https://github.com/amueller/word_cloud
- JSON-LD - especificação W3C: https://www.w3.org/TR/json-ld/
- Schema.org - vocabulário para dados estruturados: https://schema.org/
- Enunciado do trabalho e slides do prof. - UEM, Departamento de Informática

---

# Obrigado!