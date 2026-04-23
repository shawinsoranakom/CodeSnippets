def update_outdated(
    language: Annotated[str, typer.Option(envvar="LANGUAGE")],
    max: Annotated[int, typer.Option(envvar="MAX")] = 10,
) -> None:
    outdated_paths = list_outdated(language)
    for path in outdated_paths[:max]:
        print(f"Updating lang: {language} path: {path}")
        translate_page(language=language, en_path=path)
        print(f"Done updating: {path}")
    print("Done updating all outdated paths")