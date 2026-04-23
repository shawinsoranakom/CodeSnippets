def _load_reduce_documents_chain(config: dict, **kwargs: Any) -> ReduceDocumentsChain:
    combine_documents_chain = None
    collapse_documents_chain = None

    if "combine_documents_chain" in config:
        combine_document_chain_config = config.pop("combine_documents_chain")
        combine_documents_chain = load_chain_from_config(
            combine_document_chain_config,
            **kwargs,
        )
    elif "combine_document_chain" in config:
        combine_document_chain_config = config.pop("combine_document_chain")
        combine_documents_chain = load_chain_from_config(
            combine_document_chain_config,
            **kwargs,
        )
    elif "combine_documents_chain_path" in config:
        combine_documents_chain = load_chain(
            config.pop("combine_documents_chain_path"),
            **kwargs,
        )
    elif "combine_document_chain_path" in config:
        combine_documents_chain = load_chain(
            config.pop("combine_document_chain_path"),
            **kwargs,
        )
    else:
        msg = (
            "One of `combine_documents_chain` or "
            "`combine_documents_chain_path` must be present."
        )
        raise ValueError(msg)

    if "collapse_documents_chain" in config:
        collapse_document_chain_config = config.pop("collapse_documents_chain")
        if collapse_document_chain_config is None:
            collapse_documents_chain = None
        else:
            collapse_documents_chain = load_chain_from_config(
                collapse_document_chain_config,
                **kwargs,
            )
    elif "collapse_documents_chain_path" in config:
        collapse_documents_chain = load_chain(
            config.pop("collapse_documents_chain_path"),
            **kwargs,
        )
    elif "collapse_document_chain" in config:
        collapse_document_chain_config = config.pop("collapse_document_chain")
        if collapse_document_chain_config is None:
            collapse_documents_chain = None
        else:
            collapse_documents_chain = load_chain_from_config(
                collapse_document_chain_config,
                **kwargs,
            )
    elif "collapse_document_chain_path" in config:
        collapse_documents_chain = load_chain(
            config.pop("collapse_document_chain_path"),
            **kwargs,
        )

    return ReduceDocumentsChain(
        combine_documents_chain=combine_documents_chain,
        collapse_documents_chain=collapse_documents_chain,
        **config,
    )