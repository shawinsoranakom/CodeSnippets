def remove_removable(language: Annotated[str, typer.Option(envvar="LANGUAGE")]) -> None:
    removable_paths = list_removable(language)
    for path in removable_paths:
        path.unlink()
        print(f"Removed: {path}")
    print("Done removing all removable paths")