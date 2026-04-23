def collect_input_documents(
    input_path: Path,
    start_page_id: int,
    end_page_id: Optional[int],
) -> list[InputDocument]:
    documents: list[Path]
    if input_path.is_dir():
        documents = [path for path in sorted(input_path.glob("*")) if path.is_file()]
    else:
        documents = [input_path]

    collected: list[InputDocument] = []
    for order, path in enumerate(documents):
        suffix = guess_suffix_by_path(path)
        if suffix not in pdf_suffixes + image_suffixes + office_suffixes:
            continue

        if suffix in pdf_suffixes:
            effective_pages = probe_pdf_effective_pages(
                path,
                start_page_id=start_page_id,
                end_page_id=end_page_id,
            )
        else:
            effective_pages = 1

        collected.append(
            InputDocument(
                path=path,
                suffix=suffix,
                stem=path.stem,
                effective_pages=effective_pages,
                order=order,
            )
        )

    if not collected:
        raise click.ClickException(f"No supported documents found under {input_path}")

    normalized_stems, renamed_stems = uniquify_task_stems(
        [document.stem for document in collected]
    )
    if renamed_stems:
        rename_details = ", ".join(
            f"{document.path.name} -> {effective_stem}"
            for document, effective_stem in zip(collected, normalized_stems)
            if document.stem != effective_stem
        )
        logger.warning(
            f"Normalized duplicate document stems within this run: {rename_details}"
        )
        return [
            InputDocument(
                path=document.path,
                suffix=document.suffix,
                stem=effective_stem,
                effective_pages=document.effective_pages,
                order=document.order,
            )
            for document, effective_stem in zip(collected, normalized_stems)
        ]

    return collected