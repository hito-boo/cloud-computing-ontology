import os
import re
import math
from collections import Counter, defaultdict
from typing import Dict, List, Optional, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.colors as mcolors
import numpy as np

try:
    from wordcloud import WordCloud
    _HAS_WORDCLOUD = True
except ImportError:
    _HAS_WORDCLOUD = False
    print("[warn] wordcloud not installed. Run: pip install wordcloud")

# Paleta principal
_COLORS = [
    "#2E86AB", "#A23B72", "#F18F01", "#C73E1D", "#3B1F2B",
    "#44BBA4", "#E94F37", "#393E41", "#F5C518", "#6B4226",
    "#8338EC", "#06D6A0", "#FF006E", "#FB5607", "#3A86FF",
]
_CMAP_HEATMAP = "YlOrRd"

# Técnicas de Cloud Computing / Segurança para detecção por busca de termos.
# Chave = nome legível para o eixo; valor = lista de strings a buscar (lowercase).
CLOUD_SECURITY_TECHNIQUES: Dict[str, List[str]] = {
    "Attribute-Based Enc. (ABE)": ["attribute-based encryption", "abe", "cp-abe", "kp-abe"],
    "Searchable Encryption": ["searchable encryption", "sse", "peks", "xse"],
    "Data Integrity / Auditing": ["data integrity", "auditing", "proof of retrievability", "por", "pdp", "provable data"],
    "Access Control": ["access control", "rbac", "acl", "policy"],
    "Intrusion Detection (IDS)": ["intrusion detection", " ids ", "anomaly detection", "misuse detection"],
    "Machine/Deep Learning": ["machine learning", "deep learning", "neural network", "random forest", "classification", "svm"],
    "Authentication": ["authentication", "two-factor", "multi-factor", "mfa", "biometric", "fingerprint"],
    "Homomorphic Encryption": ["homomorphic"],
    "Digital Signature / PKI": ["digital signature", "pki", "certificate authority", "public key infrastructure"],
    "Cloud Storage": ["cloud storage", "cloud server", "outsourced data", "data owner"],
    "Blockchain": ["blockchain", "smart contract", "distributed ledger"],
    "Cryptographic Proofs": ["zero-knowledge", "zk-proof", "commitment scheme", "bilinear pairing"],
    "Parallel / HPC": ["high performance computing", "hpc", "parallel", "parallelization", "cluster node"],
    "Virtualization / Container": ["virtual machine", "hypervisor", "docker", "container", "kubernetes", "vm migration"],
    "IoT Security": ["iot", "internet of things", "smart device"],
    "TLS / SSL": ["tls", "ssl", " https ", "secure channel"],
    "Forensics": ["forensic", "evidence", "investigation", "artifact"],
    "Obfuscation / Code Sec.": ["obfuscat", "decompil", "code protection", "software protection"],
}

# Stop-words básicas para o tokenizador de fallback interno
_FALLBACK_STOPWORDS = {
    "the","of","and","to","in","a","is","that","for","are","this","be","as","on",
    "an","with","by","at","from","have","was","were","has","which","not","or","it",
    "also","can","we","its","our","their","these","such","been","they","will","may",
    "than","more","each","most","into","one","two","while","both","when","where",
    "but","only","any","other","all","no","if","so","up","out","about","then","how",
    "what","there","through","between","over","under","after","before","do","does",
    "used","using","use","uses","based","paper","study","article","work","proposed",
    "provide","provides","provided","approach","result","results","show","shows",
    "shown","however","thus","therefore","since","given","due","found","used","while",
}

# Gera label para uso nos gráficos
def _short_label(fname: str, paper: Dict) -> str:
    year = paper.get("metadata", {}).get("year", "????")
    authors = paper.get("authors", [])
    if authors:
        # Pega último sobrenome do primeiro autor
        surname = authors[0].split()[-1]
    else:
        # Usa parte do nome do arquivo
        surname = re.search(r"S(\d{6,})", fname)
        surname = surname.group(1)[-4:] if surname else fname[:6]
    return f"{year}\n{surname}"

# Tokenizador básico
def _fallback_tokenize(text: str) -> List[str]:
    text = text.lower()
    text = re.sub(r"[^a-z\s]", " ", text)
    return [t for t in text.split() if len(t) >= 4 and t not in _FALLBACK_STOPWORDS]

# Cria o diretório de saída
def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)

# Salva a figura e libera memória
def _save(fig: plt.Figure, output_dir: str, filename: str) -> None:
    path = os.path.join(output_dir, filename)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  [saved] {filename}")

# Gráfico de barras horizontais
def _horizontal_bar(counter: Counter, top_n: int, title: str, xlabel: str, color: str, output_dir: str, filename: str) -> None:
    items = counter.most_common(top_n)
    if not items:
        print(f"  [skip] {filename} - no data")
        return

    labels = [it[0] for it in items][::-1]
    values = [it[1] for it in items][::-1]
    max_v = max(values) or 1

    fig, ax = plt.subplots(figsize=(9, max(4, top_n * 0.42)))
    bars = ax.barh(labels, values, color=color, edgecolor="white", linewidth=0.5)

    # Valor na ponta de cada barra
    for bar, val in zip(bars, values):
        ax.text(
            val + max_v * 0.01, bar.get_y() + bar.get_height() / 2,
            str(val), va="center", ha="left", fontsize=8,
        )

    ax.set_xlabel(xlabel, fontsize=10)
    ax.set_title(title, fontsize=13, fontweight="bold", pad=10)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.set_xlim(0, max_v * 1.14)

    _save(fig, output_dir, filename)

# Bar Chart dos termos mais frequentes
def plot_top_terms_bar(tokens_all: List[str], top_n: int = 15, output_dir: str = "visualizations") -> None:
    _horizontal_bar(
        Counter(tokens_all), top_n,
        title=f"Top {top_n} Most Frequent Terms (Corpus)",
        xlabel="Frequency (occurrences)",
        color=_COLORS[0],
        output_dir=output_dir,
        filename="1_bar_top_terms.png",
    )

# Nuvem de palavras geral
def plot_wordcloud(tokens_all: List[str], output_dir: str = "visualizations", title: str = "Word Cloud - Cloud Computing & Security Corpus", filename: str = "2_wordcloud_general.png") -> None:
    if not _HAS_WORDCLOUD:
        print("  [skip] wordcloud - install with: pip install wordcloud")
        return

    freq = Counter(tokens_all)
    if not freq:
        print("  [skip] wordcloud - no tokens")
        return

    wc = WordCloud(
        width=1200, height=600,
        background_color="white",
        colormap="Blues",
        max_words=120,
        collocations=False,
        prefer_horizontal=0.9,
    ).generate_from_frequencies(freq)

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.imshow(wc, interpolation="bilinear")
    ax.axis("off")
    ax.set_title(title, fontsize=14, fontweight="bold", pad=10)

    _save(fig, output_dir, filename)

# Detecta técnicas pré-definidas e desenha um Bar Chart de frequência
def plot_techniques_frequency(categorized_corpus: Dict[str, Dict], output_dir: str = "visualizations") -> None:
    # Conta quantas vezes cada técnica aparece (somando todos os artigos)
    counts: Counter = Counter()
    for paper in categorized_corpus.values():
        text = (paper.get("abstract", "") + " " + paper.get("body_text", "")).lower()
        for technique, keywords in CLOUD_SECURITY_TECHNIQUES.items():
            mentions = sum(text.count(kw) for kw in keywords)
            if mentions:
                counts[technique] += mentions

    _horizontal_bar(
        counts, len(counts),
        title="Techniques Most Mentioned Across the Corpus",
        xlabel="Total Mentions",
        color=_COLORS[1],
        output_dir=output_dir,
        filename="3_bar_techniques.png",
    )

# Desenha um Heat Map com a evolução temporal dos termos
def plot_temporal_evolution(categorized_corpus: Dict[str, Dict], tokens_per_article: Dict[str, List[str]], top_n: int = 14, output_dir: str = "visualizations") -> None:
    # Agrupa tokens por ano de publicação
    year_tokens: Dict[str, List[str]] = defaultdict(list)
    for fname, paper in categorized_corpus.items():
        year = paper.get("metadata", {}).get("year", "")
        if year and fname in tokens_per_article:
            year_tokens[year].extend(tokens_per_article[fname])

    if len(year_tokens) < 2:
        print("  [skip] temporal heatmap - fewer than 2 distinct years")
        return

    # Determina os termos globais mais frequentes para as linhas do Heat Map
    all_tokens: List[str] = []
    for tks in tokens_per_article.values():
        all_tokens.extend(tks)
    top_terms = [t for t, _ in Counter(all_tokens).most_common(top_n)]

    sorted_years = sorted(year_tokens.keys())
    # Monta a matriz (termos x anos), cada célula = % do total do ano
    matrix = np.zeros((len(top_terms), len(sorted_years)))
    for j, year in enumerate(sorted_years):
        year_cnt = Counter(year_tokens[year])
        total = sum(year_cnt.values()) or 1
        for i, term in enumerate(top_terms):
            matrix[i, j] = year_cnt.get(term, 0) / total * 100

    fig, ax = plt.subplots(figsize=(max(8, len(sorted_years) * 1.1), max(6, top_n * 0.52)))
    im = ax.imshow(matrix, cmap=_CMAP_HEATMAP, aspect="auto")

    ax.set_xticks(range(len(sorted_years)))
    ax.set_xticklabels(sorted_years, fontsize=10, fontweight="bold")
    ax.set_yticks(range(len(top_terms)))
    ax.set_yticklabels(top_terms, fontsize=9)

    # Valores nas células (omite zeros)
    vmax = matrix.max() or 1
    for i in range(len(top_terms)):
        for j in range(len(sorted_years)):
            v = matrix[i, j]
            if v > 0:
                color = "white" if v > vmax * 0.58 else "black"
                ax.text(j, i, f"{v:.1f}", ha="center", va="center",
                        fontsize=7, color=color)

    # Indica quantos artigos há por ano
    for j, year in enumerate(sorted_years):
        # Conta artigos com esse ano
        n_arts = sum(
            1 for p in categorized_corpus.values()
            if p.get("metadata", {}).get("year", "") == year
        )
        ax.text(j, -0.8, f"n={n_arts}", ha="center", va="top",
                fontsize=7, color="gray")

    cbar = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.04)
    cbar.set_label("Relative frequency (%)", fontsize=9)

    ax.set_title("Temporal Evolution of Top Terms (% per year)", fontsize=13,
                 fontweight="bold", pad=18)
    ax.set_xlabel("Publication Year", fontsize=10)
    ax.set_ylabel("Term", fontsize=10)

    _save(fig, output_dir, "4_heatmap_temporal.png")

# Desenha gráfico com termos presentes na seção de trabalhos futuros
def plot_future_work_terms(stage2_corpus: Dict[str, Dict], output_dir: str = "visualizations") -> None:
    raw_text = " ".join(
        " ".join(info.get("future_work", []))
        for info in stage2_corpus.values()
    )
    if not raw_text.strip():
        print("  [skip] future work - no sentences found in stage2")
        return

    # Tokenização leve sobre o texto de futuros trabalhos
    fw_tokens = _fallback_tokenize(raw_text)
    extra_stop = {
        "will", "plan", "future", "work", "research", "further", "also",
        "currently", "next", "extend", "plan", "plans", "planned",
    }
    fw_tokens = [t for t in fw_tokens if t not in extra_stop]

    if not fw_tokens:
        print("  [skip] future work - all tokens were stopwords")
        return

    # Bar Chart
    _horizontal_bar(
        Counter(fw_tokens), 15,
        title="Most Frequent Terms in Future Work Sections",
        xlabel="Occurrences",
        color=_COLORS[3],
        output_dir=output_dir,
        filename="5a_bar_future_work.png",
    )

    # Word Cloud
    plot_wordcloud(
        fw_tokens,
        output_dir=output_dir,
        title="Word Cloud - Future Work",
        filename="5b_wordcloud_future_work.png",
    )

# Coocorrência de termos
def plot_cooccurrence_heatmap(tokens_per_article: Dict[str, List[str]], top_n: int = 14, window: int = 5, output_dir: str = "visualizations") -> None:
    all_tokens: List[str] = []
    for tks in tokens_per_article.values():
        all_tokens.extend(tks)

    top_terms = [t for t, _ in Counter(all_tokens).most_common(top_n)]
    term_idx = {t: i for i, t in enumerate(top_terms)}

    # Contagem de coocorrência via janela deslizante em cada artigo
    matrix = np.zeros((top_n, top_n), dtype=float)
    for tokens in tokens_per_article.values():
        for center, tok in enumerate(tokens):
            if tok not in term_idx:
                continue
            i = term_idx[tok]
            lo = max(0, center - window)
            hi = min(len(tokens), center + window + 1)
            for k in range(lo, hi):
                if k == center:
                    continue
                if tokens[k] in term_idx:
                    j = term_idx[tokens[k]]
                    matrix[i, j] += 1

    # Normaliza pela diagonal (auto-frequência) para obter correlação relativa
    diag = np.diag(matrix).copy()
    diag[diag == 0] = 1
    matrix_norm = matrix / diag[:, np.newaxis] # Fração de coocorrência

    fig, ax = plt.subplots(figsize=(10, 9))
    im = ax.imshow(matrix_norm, cmap="Blues", aspect="auto", vmin=0)

    ax.set_xticks(range(top_n))
    ax.set_xticklabels(top_terms, rotation=45, ha="right", fontsize=8)
    ax.set_yticks(range(top_n))
    ax.set_yticklabels(top_terms, fontsize=8)

    # Valores nas células
    vmax = matrix_norm.max() or 1
    for i in range(top_n):
        for j in range(top_n):
            v = matrix_norm[i, j]
            if v > 0.02:
                col = "white" if v > vmax * 0.6 else "black"
                ax.text(j, i, f"{v:.2f}", ha="center", va="center",
                        fontsize=6.5, color=col)

    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("Co-occurrence ratio (window=" + str(window) + ")", fontsize=9)

    ax.set_title(f"Term Co-occurrence Heatmap (top {top_n} terms, window={window})", fontsize=12, fontweight="bold", pad=10)

    _save(fig, output_dir, "6_heatmap_cooccurrence.png")

# Heat Map da similaridade de Jaccard entre pares de artigos
def plot_article_similarity_heatmap(categorized_corpus: Dict[str, Dict], tokens_per_article: Dict[str, List[str]], output_dir: str = "visualizations") -> None:
    fnames = list(tokens_per_article.keys())
    n = len(fnames)
    if n < 2:
        print("  [skip] similarity heatmap - need at least 2 articles")
        return

    sets = [set(tokens_per_article[f]) for f in fnames]
    labels = [_short_label(f, categorized_corpus.get(f, {})) for f in fnames]
    matrix = np.zeros((n, n))

    # Jaccard para cada par
    for i in range(n):
        for j in range(n):
            inter = len(sets[i] & sets[j])
            union = len(sets[i] | sets[j])
            matrix[i, j] = inter / union if union else 0.0

    fig, ax = plt.subplots(figsize=(11, 9))
    im = ax.imshow(matrix, cmap="YlGnBu", vmin=0, vmax=1)

    ax.set_xticks(range(n))
    ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=7.5)
    ax.set_yticks(range(n))
    ax.set_yticklabels(labels, fontsize=7.5)

    for i in range(n):
        for j in range(n):
            v = matrix[i, j]
            col = "white" if v > 0.55 else "black"
            ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=7, color=col)

    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("Jaccard similarity", fontsize=9)

    ax.set_title("Article Similarity Heatmap (Jaccard on token sets)", fontsize=12, fontweight="bold", pad=10)

    _save(fig, output_dir, "7a_heatmap_similarity.png")

# Diagrama de similaridade entre artigos
def plot_article_similarity_network(categorized_corpus: Dict[str, Dict], tokens_per_article: Dict[str, List[str]], threshold: float = 0.18, output_dir: str = "visualizations") -> None:
    fnames = list(tokens_per_article.keys())
    n = len(fnames)
    if n < 2:
        return

    sets = [set(tokens_per_article[f]) for f in fnames]
    labels = [_short_label(f, categorized_corpus.get(f, {})) for f in fnames]

    # Posições em círculo
    angles = [2 * math.pi * i / n for i in range(n)]
    xs = [math.cos(a) for a in angles]
    ys = [math.sin(a) for a in angles]

    fig, ax = plt.subplots(figsize=(11, 10))
    ax.set_aspect("equal")
    ax.axis("off")

    # Arestas
    max_sim = 0.0
    edges: List[Tuple[int, int, float]] = []
    for i in range(n):
        for j in range(i + 1, n):
            inter = len(sets[i] & sets[j])
            union = len(sets[i] | sets[j])
            sim = inter / union if union else 0.0
            if sim >= threshold:
                edges.append((i, j, sim))
                if sim > max_sim:
                    max_sim = sim

    if not edges:
        print(f"  [info] no article pairs above threshold {threshold} - lowering to 0.10")
        threshold = 0.10
        for i in range(n):
            for j in range(i + 1, n):
                inter = len(sets[i] & sets[j])
                union = len(sets[i] | sets[j])
                sim = inter / union if union else 0.0
                if sim >= threshold:
                    edges.append((i, j, sim))
                    if sim > max_sim:
                        max_sim = sim

    for (i, j, sim) in edges:
        alpha = 0.2 + 0.7 * (sim / max(max_sim, 0.01))
        lw = 0.5 + 4.0 * (sim / max(max_sim, 0.01))
        ax.plot([xs[i], xs[j]], [ys[i], ys[j]], color=_COLORS[0], alpha=alpha, lw=lw, zorder=1)
        # Rótulo no meio da aresta com o valor de similaridade
        mx, my = (xs[i] + xs[j]) / 2, (ys[i] + ys[j]) / 2
        ax.text(mx, my, f"{sim:.2f}", fontsize=6, ha="center", va="center", color="gray", zorder=2)

    # Nós
    cmap = plt.cm.get_cmap("tab10", n)
    for i in range(n):
        ax.scatter(xs[i], ys[i], s=450, color=cmap(i), zorder=3, edgecolors="white", linewidths=1.5)
        # Rótulo do artigo (fora do nó, alinhado radialmente)
        offset = 0.18
        lx = xs[i] * (1 + offset)
        ly = ys[i] * (1 + offset)
        ha = "left" if xs[i] > 0.1 else ("right" if xs[i] < -0.1 else "center")
        ax.text(lx, ly, labels[i], fontsize=7.5, ha=ha, va="center", fontweight="bold", zorder=4)

    ax.set_title(f"Article Similarity Network (Jaccard ≥ {threshold:.2f})", fontsize=13, fontweight="bold", pad=12)
    # Legenda de espessura da aresta
    legend_handles = [mpatches.Patch(facecolor=_COLORS[0], alpha=0.4, label=f"Similarity ≥ {threshold:.2f}")]
    ax.legend(handles=legend_handles, loc="lower right", fontsize=8)

    ax.set_xlim(-1.45, 1.45)
    ax.set_ylim(-1.45, 1.45)

    _save(fig, output_dir, "7b_network_similarity.png")

# Árvore de palavras
def plot_word_tree(tokens_per_article: Dict[str, List[str]], pivot: str = "cloud", n_branches: int = 10, output_dir: str = "visualizations") -> None:
    before_counter: Counter = Counter()
    after_counter: Counter = Counter()

    for tokens in tokens_per_article.values():
        for i, tok in enumerate(tokens):
            if tok == pivot:
                if i > 0:
                    before_counter[tokens[i - 1]] += 1
                if i < len(tokens) - 1:
                    after_counter[tokens[i + 1]] += 1

    if not before_counter and not after_counter:
        print(f"  [skip] word tree - pivot '{pivot}' not found in corpus")
        return

    top_before = before_counter.most_common(n_branches)[::-1]   # menor freq em cima
    top_after = after_counter.most_common(n_branches)[::-1]

    # Layout: 2 sub-plots lado a lado, compartilhando o eixo Y central
    fig, (ax_l, ax_c, ax_r) = plt.subplots(
        1, 3,
        figsize=(13, max(5, n_branches * 0.45)),
        gridspec_kw={"width_ratios": [4, 1.2, 4]},
    )

    def _side_bar(ax, items, is_left: bool) -> None:
        if not items:
            ax.axis("off")
            return
        labels = [it[0] for it in items]
        values = [it[1] for it in items]
        max_v = max(values) or 1
        y_pos = range(len(labels))

        cmap_local = plt.cm.Blues
        colors = [cmap_local(0.35 + 0.55 * v / max_v) for v in values]
        bars = ax.barh(list(y_pos), values if not is_left else [-v for v in values], color=colors, edgecolor="white", linewidth=0.4)

        for bar, label, val in zip(bars, labels, values):
            x_txt = -val - max_v * 0.02 if is_left else val + max_v * 0.02
            ha = "right" if is_left else "left"
            ax.text(x_txt, bar.get_y() + bar.get_height() / 2, f"{label}  ({val})", va="center", ha=ha, fontsize=8.5)

        ax.set_yticks(list(y_pos))
        ax.set_yticklabels([""] * len(labels))
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_visible(False)
        if is_left:
            ax.set_xlim(-max_v * 1.5, 0)
            ax.spines["bottom"].set_visible(False)
            ax.set_xticks([])
        else:
            ax.set_xlim(0, max_v * 1.5)
            ax.spines["bottom"].set_visible(False)
            ax.set_xticks([])

    _side_bar(ax_l, top_before, is_left=True)
    _side_bar(ax_r, top_after, is_left=False)

    # Coluna central: apenas o pivot
    ax_c.axis("off")
    ax_c.text(0.5, 0.5, f'"{pivot}"',
              ha="center", va="center", fontsize=14, fontweight="bold",
              transform=ax_c.transAxes,
              bbox=dict(boxstyle="round,pad=0.5", facecolor=_COLORS[4], edgecolor="white", alpha=0.85))
    ax_c.text(0.5, 0.1, "←  precedes  |  follows  →",
              ha="center", va="bottom", fontsize=7.5, color="gray",
              transform=ax_c.transAxes)

    fig.suptitle(
        f"Word Tree - context of \"{pivot}\" in the corpus",
        fontsize=13, fontweight="bold", y=1.01,
    )

    _save(fig, output_dir, f"8_word_tree_{pivot}.png")

# Gerar todas as visualizações
def generate_all_visualizations(
    categorized_corpus: Dict[str, Dict],
    stage2_corpus: Dict[str, Dict],
    tokens_per_article: Optional[Dict[str, List[str]]] = None,
    output_dir: str = "visualizations",
    word_tree_pivot: str = "cloud",
    top_n_terms: int = 15,
    top_n_temporal: int = 14,
    cooccurrence_window: int = 5,
    similarity_threshold: float = 0.18,
) -> None:
    _ensure_dir(output_dir)

    # Usa o tokenizador simples se tokens não forem fornecidos
    if tokens_per_article is None:
        print("[info] tokens_per_article not provided - using fallback tokenizer")
        tokens_per_article = {
            fname: _fallback_tokenize(paper.get("body_text", ""))
            for fname, paper in categorized_corpus.items()
        }

    # Token list global (todos os artigos concatenados)
    all_tokens: List[str] = []
    for tks in tokens_per_article.values():
        all_tokens.extend(tks)

    print(f"\n[visualizations] corpus: {len(categorized_corpus)} articles, "
          f"{len(all_tokens):,} total tokens")
    print(f"[visualizations] output dir: {os.path.abspath(output_dir)}\n")

    # 1 - Bar: palavras mais citadas
    print("1/8 - Top terms bar chart")
    plot_top_terms_bar(all_tokens, top_n=top_n_terms, output_dir=output_dir)

    # 2 - Word cloud geral
    print("2/8 - General word cloud")
    plot_wordcloud(all_tokens, output_dir=output_dir)

    # 3 - Técnicas mais mencionadas
    print("3/8 - Techniques frequency")
    plot_techniques_frequency(categorized_corpus, output_dir=output_dir)

    # 4 - Evolução temporal
    print("4/8 - Temporal evolution heatmap")
    plot_temporal_evolution(categorized_corpus, tokens_per_article, top_n=top_n_temporal, output_dir=output_dir)

    # 5 - Trabalhos futuros
    print("5/8 - Future work terms")
    plot_future_work_terms(stage2_corpus, output_dir=output_dir)

    # 6 - Co-ocorrência
    print("6/8 - Co-occurrence heatmap")
    plot_cooccurrence_heatmap(tokens_per_article, top_n=top_n_terms, window=cooccurrence_window, output_dir=output_dir)

    # 7a - Heatmap de similaridade
    print("7a/8 - Article similarity heatmap")
    plot_article_similarity_heatmap(categorized_corpus, tokens_per_article, output_dir=output_dir)

    # 7b - Network de similaridade
    print("7b/8 - Article similarity network")
    plot_article_similarity_network(categorized_corpus, tokens_per_article, threshold=similarity_threshold, output_dir=output_dir)

    # 8 - Word tree
    print(f"8/8  - Word tree (pivot='{word_tree_pivot}')")
    plot_word_tree(tokens_per_article, pivot=word_tree_pivot, n_branches=10, output_dir=output_dir,)

    print(f"\n[done] All visualizations saved to: {os.path.abspath(output_dir)}/")