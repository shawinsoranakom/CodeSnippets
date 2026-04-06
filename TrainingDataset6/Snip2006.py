def update_and_add(
    language: Annotated[str, typer.Option(envvar="LANGUAGE")],
    max: Annotated[int, typer.Option(envvar="MAX")] = 10,
) -> None:
    print(f"Updating outdated translations for {language}")
    update_outdated(language=language, max=max)
    print(f"Adding missing translations for {language}")
    add_missing(language=language, max=max)
    print(f"Done updating and adding for {language}")