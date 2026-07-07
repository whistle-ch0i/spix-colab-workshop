#!/usr/bin/env python3
"""Write the KOGO-style downstream spatial analysis notebook."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from write_korean_workshop_notebook import (
    BAYESSPACE_LABELS_FILE,
    COMBINED_NOTEBOOK,
    DATA_FILE,
    DEFAULT_BAYESSPACE_LABELS_URL,
    DEFAULT_BOOTSTRAP_URL,
    DEFAULT_DATA_URL,
    DEFAULT_HELPER_URL,
    DEFAULT_LIANA_RESULTS_URL,
    DEFAULT_NOTEBOOK_DIR,
    DEFAULT_ONTOLOGY_LAYER_URL,
    DEFAULT_ONTOLOGY_REFERENCE_URL,
    DEFAULT_REQUIREMENTS_URL,
    DEFAULT_ROI_CONTEXT_URL,
    DEFAULT_SPAGCN_LABELS_URL,
    DEFAULT_SPIX_INSTALL_URL,
    LIANA_RESULTS_FILE,
    ONTOLOGY_LAYER_FILE,
    ONTOLOGY_REFERENCE_FILE,
    ROI_CONTEXT_FILE,
    SPAGCN_LABELS_FILE,
    cci_cells,
    code,
    data_cells,
    domain_cells,
    eight_um_cells,
    final_cells,
    md,
    new_notebook,
    setup_cells,
    sha256sum,
    spix_cells,
    write_notebook,
)


KOGO_DOWNSTREAM_NOTEBOOK = "Choi_Whisoo_KOGO_spatial_downstream_colab.ipynb"


def kogo_intro_cells() -> list:
    return [
        md(
            """
            # KOGO 워크샵 — 공간전사체 downstream 분석

            이 노트북은 앞선 실습에서 다룬 deconvolution, cell segmentation,
            cell typing 결과를 다음 분석 질문으로 이어가는 파트입니다.

            앞쪽 노트북에서 다룬 흐름은 대략 아래와 같습니다.

            1. Visium: spot 단위 deconvolution으로 조직 내 세포 조성 추정
            2. Visium HD: 2 um bin과 H&E 기반 segmentation으로 더 작은 단위 복원
            3. Xenium: cell segmentation과 label transfer로 cell 단위 annotation 생성

            여기서는 같은 공간전사체 데이터에서 downstream 질문을 이어갑니다.

            1. SVG: 공간적으로 정리된 gene을 찾고, DEG/module/pathway 관점으로 해석
            2. Spatial domain: expression-only clustering과 spatial method의 차이 확인
            3. CCI: 서로 붙어 있는 domain 사이의 ligand-receptor 신호 확인
            4. SPIX: 2 um 정보를 여러 scale의 tissue unit으로 바꾸고 scale별 SVG 해석

            오늘 실습에서 실제로 실행하는 기본 데이터는 Visium HD P2 ROI입니다.
            Xenium이나 segmentation 결과는 같은 downstream 질문이 cell 단위로도
            이어진다는 연결부로 설명합니다. Colab 현장에서는 실행 안정성이 더
            중요하므로, 무거운 외부 설치가 필요한 부분은 미리 계산한 결과를
            checksum으로 확인한 뒤 읽습니다.
            """
        ),
        md(
            """
            ### 분석 흐름

            - **입력 단위**: 앞선 파트의 output은 spot, 8 um bin, cell 등 서로 다를 수 있습니다.
            - **공통 질문**: 어떤 gene/program이 공간적으로 정리되어 있는가?
            - **공간 정보의 역할**: expression만으로 나눈 cluster와 실제 조직 위에서 이어지는 domain은 다를 수 있습니다.
            - **해석 단위**: domain을 잡은 뒤 DEG, pathway-like gene program, CCI로 생물학적 의미를 붙입니다.
            - **SPIX**: 고해상도 2 um 정보를 여러 scale의 tissue unit으로 바꿔 같은 질문을 다시 봅니다.

            이 노트북은 코드를 길게 숨기지 않고, 한 셀에서 한 가지 분석만 하도록
            구성했습니다. 파라미터는 각 tool 소개 cell에서 먼저 보고, 바로 다음
            code cell에서 확인합니다.
            """
        ),
        md(
            """
            ### 대표 논문

            이론 강의자료 업데이트용으로 아래 논문들을 같이 보면 좋습니다. PDF
            파일과 링크 manifest는 repo의 `references/` 폴더에 따로 정리합니다.

            - SVG / 공간 자기상관: SpatialDE, SPARK, Squidpy, Moran's I
            - Spatial domain: BayesSpace, SpaGCN, BANKSY
            - CCI: CellPhoneDB, CellChat, LIANA/LIANA+, COMMOT
            - 고해상도/segmentation: Visium HD, Xenium, bin2cell, Cellpose, SLIC/SPIX
            """
        ),
    ]


def kogo_svg_cells() -> list:
    return [
        md(
            """
            ## 4. SVG

            여기서 SVG를 구하는 이유는 gene list 하나를 더 만들기 위해서가 아닙니다.
            공간적으로 정리된 gene을 먼저 찾고, 그 gene들이 뒤에서 잡는 domain,
            DEG, module, biology와 어떻게 이어지는지 보기 위해서입니다.

            DEG는 보통 이미 정해진 group 사이의 차이를 묻습니다. 반대로 SVG는 group을
            정하기 전에 좌표를 사용해서 “조직 위에서 모여 나타나는 gene”을 찾습니다.
            그래서 SVG는 spatial domain을 해석하거나, domain marker를 고를 때 좋은
            출발점이 됩니다.

            이번 실습에서는 Squidpy의 Moran's I를 사용합니다. 값이 높을수록 가까운
            bin끼리 발현이 비슷하고, 무작위로 흩어진 패턴이 아니라는 뜻입니다.
            """
        ),
        code(
            """
            with timed_stage("svg_moran", STAGE_TIMES):
                svg_genes = list(analysis_adata.var_names)
                svg_moran = sq.gr.spatial_autocorr(
                    analysis_adata,
                    genes=svg_genes,
                    mode="moran",
                    layer="log_norm",
                    n_perms=None,
                    n_jobs=N_JOBS,
                    backend="loky",
                    copy=True,
                    show_progress_bar=False,
                )

                svg_table = svg_moran.sort_values("I", ascending=False).copy()
                svg_table["gene"] = svg_table.index
                svg_table["svg_rank"] = np.arange(1, len(svg_table) + 1)
                top_svg_genes = svg_table.head(6)["gene"].tolist()

            display(svg_table[["gene", "I", "svg_rank"]].head(20))
            """
        ),
        md(
            """
            ## 4-1. SVG 공간 패턴

            SVG는 rank table에서 끝내면 해석이 약합니다. 상위 gene을 실제 위치에
            다시 그려서, 조직 구조와 맞는 패턴인지 먼저 눈으로 확인합니다.
            """
        ),
        code(
            """
            with timed_stage("svg_gene_maps", STAGE_TIMES):
                genes_to_plot = top_svg_genes[:4]
                expression_matrix = analysis_adata.layers["log_norm"]

                fig, axes = plt.subplots(
                    1,
                    len(genes_to_plot),
                    figsize=(4.0 * len(genes_to_plot), 3.8),
                    constrained_layout=True,
                )
                if len(genes_to_plot) == 1:
                    axes = [axes]

                for ax, gene in zip(axes, genes_to_plot):
                    gene_index = analysis_adata.var_names.get_loc(gene)
                    gene_values = sparse_vector(expression_matrix, gene_index)
                    spatial_scatter(
                        ax,
                        analysis_coords,
                        values=gene_values,
                        title=gene,
                        size=3,
                        cmap="magma",
                    )
                plt.show()
            """
        ),
    ]


def svg_usage_cells() -> list:
    return [
        md(
            """
            ### SVG 활용 A — domain DEG와 비교

            SVG는 “공간적으로 모여 있는 gene”이고, DEG는 “특정 group에서 더 높은 gene”입니다.
            두 결과는 겹칠 수도 있고 다를 수도 있습니다.

            여기서는 CCI에서 사용할 fixed BayesSpace domain을 기준으로 DEG를 구하고,
            Squidpy Moran's I SVG rank와 비교합니다.

            핵심 질문은 세 가지입니다.

            - DEG이면서 SVG인 gene: domain marker이면서 공간 패턴도 뚜렷한 gene
            - DEG이지만 SVG가 약한 gene: group 차이는 있지만 공간적으로 부드럽게 이어지지는 않는 gene
            - SVG이지만 DEG가 약한 gene: 하나의 cluster marker라기보다 연속적/경계성 spatial program일 수 있는 gene
            """
        ),
        code(
            """
            with timed_stage("svg_vs_domain_deg", STAGE_TIMES):
                # CCI_CLUSTER_KEY는 domain section에서 bundled BayesSpace label로 만든 고정 domain입니다.
                sc.tl.rank_genes_groups(
                    domain_adata,
                    groupby=CCI_CLUSTER_KEY,
                    layer="log_norm",
                    use_raw=False,
                    method="t-test_overestim_var",
                    key_added="cci_domain_de",
                )
                cci_de_df = sc.get.rank_genes_groups_df(
                    domain_adata,
                    group=None,
                    key="cci_domain_de",
                )
                cci_de_df = cci_de_df.rename(columns={"names": "gene"})
                cci_de_df = cci_de_df.replace([np.inf, -np.inf], np.nan).dropna(subset=["gene"])

                # gene별로 가장 강한 domain logFC와 가장 작은 adjusted p-value만 요약합니다.
                de_gene_summary = (
                    cci_de_df
                    .assign(abs_logfoldchanges=lambda x: x["logfoldchanges"].abs())
                    .sort_values(["gene", "abs_logfoldchanges"], ascending=[True, False])
                    .groupby("gene", as_index=False)
                    .first()
                )
                de_gene_summary = de_gene_summary[[
                    "gene", "group", "scores", "logfoldchanges", "pvals_adj", "abs_logfoldchanges"
                ]]

                svg_deg_table = (
                    svg_table[["gene", "I", "svg_rank"]]
                    .merge(de_gene_summary, on="gene", how="left")
                    .sort_values("svg_rank")
                )
                svg_deg_table["is_top_svg100"] = svg_deg_table["svg_rank"] <= 100
                de_ranked = de_gene_summary.sort_values(
                    ["pvals_adj", "abs_logfoldchanges"],
                    ascending=[True, False],
                )
                top_deg100 = set(de_ranked.head(100)["gene"])
                svg_deg_table["is_top_deg100"] = svg_deg_table["gene"].isin(top_deg100)
                svg_deg_table["class"] = np.select(
                    [
                        svg_deg_table["is_top_svg100"] & svg_deg_table["is_top_deg100"],
                        svg_deg_table["is_top_svg100"] & ~svg_deg_table["is_top_deg100"],
                        ~svg_deg_table["is_top_svg100"] & svg_deg_table["is_top_deg100"],
                    ],
                    ["Top SVG + Top DEG", "SVG-prioritized", "DEG-prioritized"],
                    default="background",
                )

                svg_deg_summary = (
                    svg_deg_table["class"]
                    .value_counts()
                    .rename_axis("class")
                    .reset_index(name="n_genes")
                )
                svg_deg_table.to_csv(OUTPUT_DIR / "svg_vs_domain_deg.csv", index=False)
                svg_deg_summary.to_csv(OUTPUT_DIR / "svg_vs_domain_deg_summary.csv", index=False)

                plot_df = svg_deg_table.dropna(subset=["abs_logfoldchanges", "I"]).copy()
                plot_df["neglog10_padj"] = -np.log10(plot_df["pvals_adj"].clip(lower=1e-300))

                fig, ax = plt.subplots(figsize=(6.2, 4.6))
                color_map = {
                    "Top SVG + Top DEG": "#d55e00",
                    "SVG-prioritized": "#0072b2",
                    "DEG-prioritized": "#009e73",
                    "background": "#c7c7c7",
                }
                for label, sub in plot_df.groupby("class"):
                    ax.scatter(
                        sub["I"],
                        sub["abs_logfoldchanges"],
                        s=12 if label != "background" else 5,
                        c=color_map.get(label, "#c7c7c7"),
                        label=label,
                        alpha=0.75,
                        rasterized=True,
                    )
                for _, row in plot_df.sort_values(["is_top_svg100", "abs_logfoldchanges"], ascending=False).head(10).iterrows():
                    ax.text(row["I"], row["abs_logfoldchanges"], row["gene"], fontsize=8)
                ax.set_xlabel("Moran's I")
                ax.set_ylabel("max |domain logFC|")
                ax.set_title("SVG rank and domain DEG strength")
                ax.legend(frameon=False, fontsize=8)
                plt.show()

            display(svg_deg_summary)
            display(svg_deg_table.head(20)[[
                "gene", "I", "svg_rank", "group", "logfoldchanges", "pvals_adj", "class"
            ]])
            """
        ),
        md(
            """
            ### SVG 활용 B — SVG module 만들기

            SVG를 하나씩 보는 것도 중요하지만, 실제 해석에서는 비슷한 공간 패턴을
            가진 SVG들을 module로 묶어 보는 것이 좋습니다. 한 gene보다 gene group이
            더 안정적인 생물학 신호를 줄 때가 많기 때문입니다.

            여기서는 top SVG 80개를 domain panel 위의 expression pattern으로
            clustering합니다. 그런 다음 module별 평균 score를 조직 위에 다시
            그려서, module이 실제 공간 구조를 갖는지 봅니다.
            """
        ),
        code(
            """
            with timed_stage("svg_module_clustering", STAGE_TIMES):
                from scipy.cluster.hierarchy import linkage, fcluster, leaves_list
                from scipy.spatial.distance import pdist

                TOP_SVG_MODULE_N = int(os.environ.get("SPIX_WORKSHOP_TOP_SVG_MODULE_N", "80"))
                SVG_MODULE_K = int(os.environ.get("SPIX_WORKSHOP_SVG_MODULE_K", "4"))

                module_genes = [
                    gene for gene in svg_table.head(TOP_SVG_MODULE_N)["gene"].tolist()
                    if gene in domain_adata.var_names
                ]
                module_gene_idx = [domain_adata.var_names.get_loc(gene) for gene in module_genes]
                module_expr = domain_adata.layers["log_norm"][:, module_gene_idx]
                if sp.issparse(module_expr):
                    module_expr = module_expr.toarray()
                module_expr = np.asarray(module_expr, dtype=float)

                # gene별 z-score: module clustering은 expression scale보다 pattern을 보려는 목적입니다.
                gene_z = (module_expr - module_expr.mean(axis=0, keepdims=True))
                gene_z = gene_z / (module_expr.std(axis=0, keepdims=True) + 1e-8)
                gene_pattern = gene_z.T

                distance = pdist(gene_pattern, metric="correlation")
                linkage_matrix = linkage(distance, method="average")
                module_ids = fcluster(linkage_matrix, t=SVG_MODULE_K, criterion="maxclust")
                gene_order = leaves_list(linkage_matrix)

                svg_module_table = pd.DataFrame({
                    "gene": module_genes,
                    "svg_module": [f"M{module_id}" for module_id in module_ids],
                    "moran_i": svg_table.set_index("gene").loc[module_genes, "I"].to_numpy(),
                    "svg_rank": svg_table.set_index("gene").loc[module_genes, "svg_rank"].to_numpy(),
                }).sort_values(["svg_module", "svg_rank"])

                module_score_table = pd.DataFrame(index=domain_adata.obs_names)
                for module_id, genes_in_module in svg_module_table.groupby("svg_module")["gene"]:
                    gene_idx = [domain_adata.var_names.get_loc(gene) for gene in genes_in_module]
                    values = domain_adata.layers["log_norm"][:, gene_idx]
                    if sp.issparse(values):
                        values = values.toarray()
                    module_score_table[module_id] = np.asarray(values).mean(axis=1)

                module_score_table[CCI_CLUSTER_KEY] = domain_adata.obs[CCI_CLUSTER_KEY].astype(str).to_numpy()
                module_by_domain = module_score_table.groupby(CCI_CLUSTER_KEY).mean()
                svg_module_table.to_csv(OUTPUT_DIR / "svg_module_genes.csv", index=False)
                module_by_domain.to_csv(OUTPUT_DIR / "svg_module_scores_by_domain.csv")

                fig, axes = plt.subplots(1, 2, figsize=(11, 4.3), constrained_layout=True)
                ordered_gene_z = gene_pattern[gene_order]
                im0 = axes[0].imshow(ordered_gene_z, aspect="auto", cmap="vlag", vmin=-2, vmax=2)
                axes[0].set_title("Top SVG expression patterns")
                axes[0].set_xlabel("8 um bins in domain panel")
                axes[0].set_ylabel("SVGs ordered by module")
                fig.colorbar(im0, ax=axes[0], fraction=0.046, pad=0.04)

                im1 = axes[1].imshow(module_by_domain.to_numpy().T, aspect="auto", cmap="magma")
                axes[1].set_title("SVG module score by CCI domain")
                axes[1].set_xticks(np.arange(module_by_domain.shape[0]))
                axes[1].set_xticklabels(module_by_domain.index, rotation=45, ha="right")
                axes[1].set_yticks(np.arange(module_by_domain.shape[1]))
                axes[1].set_yticklabels(module_by_domain.columns)
                fig.colorbar(im1, ax=axes[1], fraction=0.046, pad=0.04)
                plt.show()

            display(svg_module_table.groupby("svg_module").head(8))
            """
        ),
        md(
            """
            ### SVG 활용 C — SVG module의 생물학적 해석

            여기서는 외부 pathway database를 새로 설치하지 않고, 수업 중 바로
            이해할 수 있는 CRC 관련 gene program을 작게 정의합니다. 실제 논문 분석에서는
            MSigDB, Reactome, CellMarker, HCA, Enrichr 등을 사용해 더 넓게 검증합니다.

            실습 목표는 “SVG module → 생물학적 프로그램 후보”로 넘어가는 해석 흐름을
            익히는 것입니다.
            """
        ),
        code(
            """
            with timed_stage("svg_module_program_overlap", STAGE_TIMES):
                from scipy.stats import hypergeom

                PROGRAM_GENE_SETS = {
                    "Epithelial / intestinal": {
                        "EPCAM", "KRT8", "KRT18", "KRT19", "MUC2", "MUC12", "TFF3",
                        "CLCA1", "FCGBP", "PIGR", "OLFM4", "REG1A", "REG1B", "PHGR1",
                    },
                    "Stem / proliferative": {
                        "LGR5", "OLFM4", "MKI67", "TOP2A", "PCNA", "MCM2", "MCM5",
                        "MCM10", "CDK1", "UBE2C",
                    },
                    "Immune / inflammatory": {
                        "PTPRC", "LYZ", "CD74", "CXCL8", "CXCL10", "IL1B", "SPP1",
                        "APOE", "C1QA", "C1QB", "C1QC",
                    },
                    "Stromal / ECM": {
                        "COL1A1", "COL1A2", "COL3A1", "COL4A1", "FN1", "SPARC",
                        "DCN", "LUM", "BGN", "THBS2", "SFRP2", "SFRP4", "MMP2",
                    },
                    "Endothelial / vessel": {
                        "PECAM1", "VWF", "KDR", "EMCN", "RAMP2", "ENG", "ESAM",
                    },
                }

                universe = set(domain_adata.var_names)
                rows = []
                for module_id, genes in svg_module_table.groupby("svg_module")["gene"]:
                    module_gene_set = set(genes)
                    for program, program_genes in PROGRAM_GENE_SETS.items():
                        program_gene_set = set(program_genes) & universe
                        overlap = module_gene_set & program_gene_set
                        if not program_gene_set:
                            continue
                        pvalue = hypergeom.sf(
                            len(overlap) - 1,
                            len(universe),
                            len(program_gene_set),
                            len(module_gene_set),
                        )
                        rows.append({
                            "svg_module": module_id,
                            "program": program,
                            "n_module_genes": len(module_gene_set),
                            "n_program_genes": len(program_gene_set),
                            "n_overlap": len(overlap),
                            "pvalue": pvalue,
                            "overlap_genes": ", ".join(sorted(overlap)),
                        })

                module_program_table = pd.DataFrame(rows)
                module_program_table["neglog10_p"] = -np.log10(module_program_table["pvalue"].clip(lower=1e-300))
                module_program_table = module_program_table.sort_values(
                    ["svg_module", "pvalue", "n_overlap"],
                    ascending=[True, True, False],
                )
                module_program_table.to_csv(OUTPUT_DIR / "svg_module_program_overlap.csv", index=False)

                module_program_heatmap = module_program_table.pivot_table(
                    index="program",
                    columns="svg_module",
                    values="neglog10_p",
                    fill_value=0,
                    aggfunc="max",
                )

                fig, ax = plt.subplots(figsize=(6.4, 4.2))
                im = ax.imshow(module_program_heatmap.to_numpy(), aspect="auto", cmap="viridis")
                ax.set_xticks(np.arange(module_program_heatmap.shape[1]))
                ax.set_xticklabels(module_program_heatmap.columns)
                ax.set_yticks(np.arange(module_program_heatmap.shape[0]))
                ax.set_yticklabels(module_program_heatmap.index)
                ax.set_title("SVG module program overlap")
                fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04, label="-log10 p")
                plt.show()

            display(module_program_table.groupby("svg_module").head(3))
            """
        ),
    ]


def domain_interpretation_cells() -> list:
    return [
        md(
            """
            ### Spatial domain 해석 A — expression-only와 무엇이 다른가

            Spatial domain tool을 쓰는 이유는 예쁜 그림을 얻기 위해서가 아닙니다.
            expression-only clustering은 비슷한 발현을 가진 bin을 묶지만, 그 bin들이
            조직 위에서 이어져 있는지는 따로 보지 않습니다. Spatial method는 발현과
            위치를 함께 보면서 tissue architecture를 더 직접적으로 반영합니다.

            아래에서는 각 방법의 label이 공간 neighbor graph 위에서 얼마나 같은 label끼리
            붙어 있는지 간단히 비교합니다. 이 값이 높다고 항상 좋은 것은 아니지만,
            expression-only 결과와 spatial domain 결과가 무엇을 다르게 강제하는지
            이해하는 데 도움이 됩니다.
            """
        ),
        code(
            """
            with timed_stage("domain_spatial_coherence", STAGE_TIMES):
                spatial_graph = domain_adata.obsp["squidpy_spatial_connectivities"].tocoo()
                edge_mask = spatial_graph.row < spatial_graph.col
                edge_i = spatial_graph.row[edge_mask]
                edge_j = spatial_graph.col[edge_mask]

                coherence_rows = []
                for method_name, obs_key in {
                    "Expression-only Leiden": "expression_domain",
                    "Squidpy spatial graph": "squidpy_spatial_domain",
                    "BANKSY": "banksy_domain",
                    "BayesSpace": "bayesspace_domain",
                    "SpaGCN": "spagcn_domain",
                    "CCI domain": CCI_CLUSTER_KEY,
                }.items():
                    labels = domain_adata.obs[obs_key].astype(str).to_numpy()
                    same_edge_fraction = float(np.mean(labels[edge_i] == labels[edge_j]))
                    n_clusters = int(pd.Series(labels).nunique())
                    coherence_rows.append({
                        "method": method_name,
                        "obs_key": obs_key,
                        "n_clusters": n_clusters,
                        "same_label_neighbor_fraction": same_edge_fraction,
                    })

                domain_coherence = pd.DataFrame(coherence_rows).sort_values(
                    "same_label_neighbor_fraction",
                    ascending=False,
                )
                domain_coherence.to_csv(OUTPUT_DIR / "domain_spatial_coherence.csv", index=False)

                fig, ax = plt.subplots(figsize=(6.4, 3.8))
                ax.barh(
                    domain_coherence["method"],
                    domain_coherence["same_label_neighbor_fraction"],
                    color="#4c78a8",
                )
                ax.invert_yaxis()
                ax.set_xlabel("fraction of spatial neighbor edges with same label")
                ax.set_title("Spatial coherence of domain labels")
                plt.show()

            display(domain_coherence)
            """
        ),
        md(
            """
            ### Spatial domain 해석 B — spatial method에서만 보이는 marker 후보

            이번에는 expression-only cluster DEG와 CCI domain DEG를 비교합니다.
            CCI domain에서 강하게 보이면서 expression-only top DEG에는 덜 보이는 gene은,
            공간적으로 이어진 조직 영역을 잡았을 때 더 잘 드러나는 marker 후보일 수 있습니다.

            이 표는 “spatial clustering이 expression clustering보다 항상 낫다”는 뜻이
            아닙니다. 두 방법이 다른 질문을 하고, 그 차이를 gene 단위로 확인하는
            연습입니다.
            """
        ),
        code(
            """
            with timed_stage("spatial_domain_specific_markers", STAGE_TIMES):
                sc.tl.rank_genes_groups(
                    domain_adata,
                    groupby="expression_domain",
                    layer="log_norm",
                    use_raw=False,
                    method="t-test_overestim_var",
                    key_added="expression_domain_de",
                )
                expression_de_df = sc.get.rank_genes_groups_df(
                    domain_adata,
                    group=None,
                    key="expression_domain_de",
                ).rename(columns={"names": "gene"})

                expression_top_genes = set(
                    expression_de_df.sort_values(
                        ["pvals_adj", "scores"],
                        ascending=[True, False],
                    ).head(150)["gene"]
                )

                spatial_marker_candidates = (
                    cci_de_df
                    .rename(columns={"group": "cci_domain"})
                    .merge(svg_table[["gene", "I", "svg_rank"]], on="gene", how="left")
                )
                spatial_marker_candidates = spatial_marker_candidates[
                    ~spatial_marker_candidates["gene"].isin(expression_top_genes)
                ].copy()
                spatial_marker_candidates = spatial_marker_candidates.sort_values(
                    ["pvals_adj", "I", "logfoldchanges"],
                    ascending=[True, False, False],
                )
                spatial_marker_display = spatial_marker_candidates[[
                    "cci_domain", "gene", "scores", "logfoldchanges", "pvals_adj", "I", "svg_rank"
                ]].head(25)
                spatial_marker_display.to_csv(
                    OUTPUT_DIR / "spatial_domain_specific_marker_candidates.csv",
                    index=False,
                )

            display(spatial_marker_display)
            """
        ),
        md(
            """
            ### Spatial domain 해석 C — gene program heatmap

            마지막으로 각 domain이 어떤 생물학 프로그램으로 설명되는지 봅니다.
            여기서는 앞에서 만든 작은 CRC gene program을 그대로 사용합니다.

            같은 program score를 expression-only label과 CCI domain label로 각각
            평균 내면, 공간 정보를 넣었을 때 tissue program이 더 연속적인 domain으로
            정리되는지 볼 수 있습니다.
            """
        ),
        code(
            """
            with timed_stage("domain_program_heatmap", STAGE_TIMES):
                program_score_df = pd.DataFrame(index=domain_adata.obs_names)
                for program, genes in PROGRAM_GENE_SETS.items():
                    available_genes = [gene for gene in genes if gene in domain_adata.var_names]
                    if not available_genes:
                        continue
                    gene_idx = [domain_adata.var_names.get_loc(gene) for gene in available_genes]
                    values = domain_adata.layers["log_norm"][:, gene_idx]
                    if sp.issparse(values):
                        values = values.toarray()
                    program_score_df[program] = np.asarray(values).mean(axis=1)

                expression_program = (
                    program_score_df
                    .assign(domain=domain_adata.obs["expression_domain"].astype(str).to_numpy())
                    .groupby("domain")
                    .mean()
                )
                spatial_program = (
                    program_score_df
                    .assign(domain=domain_adata.obs[CCI_CLUSTER_KEY].astype(str).to_numpy())
                    .groupby("domain")
                    .mean()
                )
                expression_program.to_csv(OUTPUT_DIR / "expression_domain_program_scores.csv")
                spatial_program.to_csv(OUTPUT_DIR / "spatial_domain_program_scores.csv")

                fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.2), constrained_layout=True)
                for ax, table, title in [
                    (axes[0], expression_program, "Expression-only domains"),
                    (axes[1], spatial_program, "Spatial CCI domains"),
                ]:
                    im = ax.imshow(table.to_numpy(), aspect="auto", cmap="magma")
                    ax.set_title(title)
                    ax.set_xticks(np.arange(table.shape[1]))
                    ax.set_xticklabels(table.columns, rotation=45, ha="right")
                    ax.set_yticks(np.arange(table.shape[0]))
                    ax.set_yticklabels(table.index)
                    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
                plt.show()

            display(spatial_program)
            """
        ),
    ]


def cci_tool_landscape_cells() -> list:
    return [
        md(
            """
            ### CCI tool map

            CCI tool은 모두 같은 질문을 하는 것처럼 보이지만 실제로는 강조점이 다릅니다.
            어떤 tool은 ligand-receptor database와 permutation을 중시하고, 어떤 tool은
            여러 scoring 방법을 합치며, 어떤 tool은 공간 거리나 downstream signal을
            더 직접적으로 봅니다.

            이 실습에서는 Colab에서 안정적으로 돌릴 수 있는 Squidpy `ligrec`와
            미리 계산한 LIANA rank-aggregate를 사용합니다. CellPhoneDB, CellChat,
            COMMOT, SpaTalk은 이론 강의와 결과 해석에서 같이 비교하면 좋습니다.
            """
        ),
        code(
            """
            cci_tool_reference = pd.DataFrame([
                {
                    "tool": "Squidpy ligrec",
                    "main_question": "cluster/domain 사이 LR pair의 평균 발현과 permutation 유의성",
                    "core_parameters": "cluster_key, interactions, threshold, n_perms",
                    "this_notebook": "live run",
                },
                {
                    "tool": "LIANA rank-aggregate",
                    "main_question": "여러 LR scoring 방법의 consensus rank",
                    "core_parameters": "resource, groupby, expr_prop, min_cells, n_perms",
                    "this_notebook": "bundled result; optional live run",
                },
                {
                    "tool": "CellPhoneDB",
                    "main_question": "curated LR complex 기반 cell group 간 communication",
                    "core_parameters": "celltype labels, expression threshold, permutations, LR database",
                    "this_notebook": "reference",
                },
                {
                    "tool": "CellChat",
                    "main_question": "LR pair를 pathway/network 단위로 요약",
                    "core_parameters": "database, group labels, min cells, pathway aggregation",
                    "this_notebook": "reference",
                },
                {
                    "tool": "COMMOT / SpaTalk",
                    "main_question": "spatial distance와 LR signal을 더 직접적으로 결합",
                    "core_parameters": "coordinates, distance kernel/cutoff, LR resource, cell/domain labels",
                    "this_notebook": "reference",
                },
            ])
            cci_tool_reference.to_csv(OUTPUT_DIR / "cci_tool_reference.csv", index=False)

            display(cci_tool_reference)
            """
        ),
    ]


def parameter_reference_cells() -> list:
    return [
        md(
            """
            ## Tool parameter quick reference

            실습 중에는 모든 파라미터를 외울 필요는 없습니다. 대신 각 tool에서
            결과를 가장 많이 바꾸는 knob가 무엇인지 알고 있어야 합니다.
            """
        ),
        code(
            """
            parameter_reference = pd.DataFrame([
                {
                    "tool": "Squidpy Moran's I",
                    "main_parameters": "spatial graph, genes, layer, n_perms",
                    "what_to_check": "neighbor 정의가 조직 구조와 맞는지; SVG rank가 실제 공간 map과 맞는지",
                },
                {
                    "tool": "SpatialDE / SPARK",
                    "main_parameters": "coordinates, expression model, covariates, multiple testing",
                    "what_to_check": "count model과 p-value calibration; 큰 데이터에서 runtime과 filtering 기준",
                },
                {
                    "tool": "BANKSY",
                    "main_parameters": "lambda, max_m, num_neighbours, resolution",
                    "what_to_check": "주변 발현을 얼마나 강하게 반영하는지; boundary가 과도하게 smooth되지 않는지",
                },
                {
                    "tool": "BayesSpace",
                    "main_parameters": "q, d, nrep, burn-in, spatial prior",
                    "what_to_check": "q 선택이 생물학적으로 해석 가능한지; MCMC 반복 수가 충분한지",
                },
                {
                    "tool": "SpaGCN",
                    "main_parameters": "adjacency, l, resolution, histology option",
                    "what_to_check": "TensorFlow import/runtime 안정성; histology를 쓸 때 image scale 정합성",
                },
                {
                    "tool": "Squidpy ligrec",
                    "main_parameters": "cluster_key, interactions, threshold, n_perms",
                    "what_to_check": "cluster label 기준이 neighborhood enrichment와 같은지",
                },
                {
                    "tool": "LIANA rank-aggregate",
                    "main_parameters": "resource, groupby, expr_prop, n_perms",
                    "what_to_check": "LR resource가 현재 gene set과 충분히 겹치는지; spatial contact와 함께 해석되는지",
                },
                {
                    "tool": "CellPhoneDB / CellChat",
                    "main_parameters": "cell/domain labels, LR database, expression threshold, permutations",
                    "what_to_check": "cell label 품질; pathway/network summary가 실제 공간 접촉과 맞는지",
                },
                {
                    "tool": "COMMOT / SpaTalk",
                    "main_parameters": "coordinates, distance cutoff/kernel, LR resource, downstream pathway option",
                    "what_to_check": "거리 제한이 조직 해상도와 맞는지; long-range 후보를 과해석하지 않는지",
                },
                {
                    "tool": "SPIX",
                    "main_parameters": "embedding dims, smoothing, equalization, target scales, compactness",
                    "what_to_check": "2 um 정보를 어느 scale에서 묶는지; scale별 SVG가 다른 biology를 보여주는지",
                },
            ])
            display(parameter_reference)
            """
        ),
    ]


def kogo_downstream_notebook(
    data_url: str,
    data_sha256: str,
    roi_context_url: str,
    roi_context_sha256: str,
    bayesspace_labels_url: str,
    bayesspace_labels_sha256: str,
    spagcn_labels_url: str,
    spagcn_labels_sha256: str,
    liana_results_url: str,
    liana_results_sha256: str,
    ontology_reference_url: str,
    ontology_reference_sha256: str,
    ontology_layer_url: str,
    ontology_layer_sha256: str,
    requirements_url: str,
    bootstrap_url: str,
    helper_url: str,
    spix_install_url: str,
):
    nb = new_notebook(KOGO_DOWNSTREAM_NOTEBOOK)
    nb["cells"] = []
    nb["cells"].extend(kogo_intro_cells())
    nb["cells"].extend(
        setup_cells(
            data_url,
            data_sha256,
            roi_context_url,
            roi_context_sha256,
            bayesspace_labels_url,
            bayesspace_labels_sha256,
            spagcn_labels_url,
            spagcn_labels_sha256,
            liana_results_url,
            liana_results_sha256,
            ontology_reference_url,
            ontology_reference_sha256,
            ontology_layer_url,
            ontology_layer_sha256,
            requirements_url,
            bootstrap_url,
            helper_url,
            spix_install_url,
        )
    )
    nb["cells"].extend(data_cells())
    nb["cells"].extend(eight_um_cells())
    nb["cells"].extend(kogo_svg_cells())
    nb["cells"].extend(domain_cells())
    nb["cells"].extend(svg_usage_cells())
    nb["cells"].extend(domain_interpretation_cells())
    nb["cells"].extend(cci_tool_landscape_cells())
    nb["cells"].extend(cci_cells())
    nb["cells"].extend(spix_cells())
    nb["cells"].extend(parameter_reference_cells())
    nb["cells"].extend(final_cells())
    return KOGO_DOWNSTREAM_NOTEBOOK, nb


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--notebook-dir", default=DEFAULT_NOTEBOOK_DIR)
    parser.add_argument("--data-file", default=f"data/{DATA_FILE}")
    parser.add_argument("--data-url", default=DEFAULT_DATA_URL)
    parser.add_argument("--roi-context-file", default=f"data/{ROI_CONTEXT_FILE}")
    parser.add_argument("--roi-context-url", default=DEFAULT_ROI_CONTEXT_URL)
    parser.add_argument("--bayesspace-labels-file", default=f"data/{BAYESSPACE_LABELS_FILE}")
    parser.add_argument("--bayesspace-labels-url", default=DEFAULT_BAYESSPACE_LABELS_URL)
    parser.add_argument("--spagcn-labels-file", default=f"data/{SPAGCN_LABELS_FILE}")
    parser.add_argument("--spagcn-labels-url", default=DEFAULT_SPAGCN_LABELS_URL)
    parser.add_argument("--liana-results-file", default=f"data/{LIANA_RESULTS_FILE}")
    parser.add_argument("--liana-results-url", default=DEFAULT_LIANA_RESULTS_URL)
    parser.add_argument("--ontology-reference-file", default=f"data/{ONTOLOGY_REFERENCE_FILE}")
    parser.add_argument("--ontology-reference-url", default=DEFAULT_ONTOLOGY_REFERENCE_URL)
    parser.add_argument("--ontology-layer-file", default=f"data/{ONTOLOGY_LAYER_FILE}")
    parser.add_argument("--ontology-layer-url", default=DEFAULT_ONTOLOGY_LAYER_URL)
    parser.add_argument("--requirements-url", default=DEFAULT_REQUIREMENTS_URL)
    parser.add_argument("--bootstrap-url", default=DEFAULT_BOOTSTRAP_URL)
    parser.add_argument("--helper-url", default=DEFAULT_HELPER_URL)
    parser.add_argument("--spix-install-url", default=DEFAULT_SPIX_INSTALL_URL)
    return parser.parse_args()


def optional_sha256(path: str) -> str:
    file_path = Path(path)
    return sha256sum(file_path) if file_path.exists() else ""


def main() -> None:
    args = parse_args()
    notebook_dir = Path(args.notebook_dir)
    name, nb = kogo_downstream_notebook(
        args.data_url,
        optional_sha256(args.data_file),
        args.roi_context_url,
        optional_sha256(args.roi_context_file),
        args.bayesspace_labels_url,
        optional_sha256(args.bayesspace_labels_file),
        args.spagcn_labels_url,
        optional_sha256(args.spagcn_labels_file),
        args.liana_results_url,
        optional_sha256(args.liana_results_file),
        args.ontology_reference_url,
        optional_sha256(args.ontology_reference_file),
        args.ontology_layer_url,
        optional_sha256(args.ontology_layer_file),
        args.requirements_url,
        args.bootstrap_url,
        args.helper_url,
        args.spix_install_url,
    )
    write_notebook(notebook_dir / name, nb)
    print(
        json.dumps(
            {
                "written": [str(notebook_dir / name)],
                "base_notebook": COMBINED_NOTEBOOK,
                "cells": len(nb["cells"]),
            },
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
