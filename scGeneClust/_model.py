# -*- coding: utf-8 -*-
# @Time : 2022/6/3 16:27
# @Author : Tory Deng
# @File : _model.py
# @Software: PyCharm
from typing import Literal, Optional

import anndata as ad
import numpy as np
from sklearn.cluster import MiniBatchKMeans

import scGeneClust.pp as pp
import scGeneClust.tl as tl
from ._utils import _check_raw_counts, set_logger, select_from_clusters, prepare_GO


def scGeneClust(
        raw_adata: ad.AnnData,
        mode: Literal['fast', 'hc'] = 'fast',
        n_components: int = 50,
        n_gene_clusters: Optional[int] = None,
        n_cell_clusters: Optional[int] = None,
        verbosity: Literal[0, 1, 2] = 1,
        random_stat: Optional[int] = None,
):
    set_logger(verbosity)
    _check_raw_counts(raw_adata)

    copied = raw_adata.copy()
    # preprocessing
    pp.preprocess(copied, mode)
    pp.reduce_dimension(copied, mode, n_components, random_stat)

    if mode == 'fast':
        km = MiniBatchKMeans(n_clusters=n_gene_clusters, random_state=random_stat)
        copied.var['cluster'] = km.fit_predict(copied.varm['pca'])  # gene clustering
        copied.var['score'] = tl.compute_gene_closeness(copied, km.cluster_centers_)
        tl.filter_adata(copied, mode, random_stat)
    else:
        tl.find_high_confidence_cells(copied, n_cell_clusters, random_stat=random_stat)
        tl.filter_adata(copied, mode, random_stat)
        # find gene cluster labels and calculate the gene-level scores
        copied.var['cluster'] = 0
        copied.var['score'] = 1

    selected_genes = select_from_clusters(copied, mode)

    # TODO: remove this preparation for GO analysis
    prepare_GO(copied, save='cache/')

    # check if all selected features are in var_names
    is_selected = np.isin(raw_adata.var_names, selected_genes)
    if is_selected.sum() != selected_genes.shape[0]:
        raise RuntimeError(f"Only found {is_selected.sum()} selected genes in adata.var_names, not {selected_genes.shape[0]}.")
    return selected_genes








