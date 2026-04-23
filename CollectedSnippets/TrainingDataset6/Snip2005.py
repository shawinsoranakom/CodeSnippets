def add_missing(
    language: Annotated[str, typer.Option(envvar="LANGUAGE")],
    max: Annotated[int, typer.Option(envvar="MAX")] = 10,
) -> None:
    missing_paths = list_missing(language)
    for path in missing_paths[:max]:
        print(f"Adding lang: {language} path: {path}")
        translate_page(language=language, en_path=path)
        print(f"Done adding: {path}")
    print("Done adding all missing paths")