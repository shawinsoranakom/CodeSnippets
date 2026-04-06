def fix_pages(
    doc_paths: Annotated[
        list[Path],
        typer.Argument(help="List of paths to documents."),
    ],
):
    all_good = True
    for path in doc_paths:
        res = process_one_page(path)
        all_good = all_good and res

    if not all_good:
        raise typer.Exit(code=1)