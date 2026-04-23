def fix_all(ctx: typer.Context, language: str):
    docs = get_all_paths(language)

    all_good = True
    for page in docs:
        doc_path = Path("docs") / language / "docs" / page
        res = process_one_page(doc_path)
        all_good = all_good and res

    if not all_good:
        raise typer.Exit(code=1)