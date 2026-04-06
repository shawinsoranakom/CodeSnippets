def update_languages() -> None:
    """
    Update the mkdocs.yml file Languages section including all the available languages.
    """
    old_config = get_en_config()
    updated_config = get_updated_config_content()
    if old_config != updated_config:
        print("docs/en/mkdocs.yml outdated")
        print("Updating docs/en/mkdocs.yml")
        en_config_path.write_text(
            yaml.dump(updated_config, sort_keys=False, width=200, allow_unicode=True),
            encoding="utf-8",
        )
        raise typer.Exit(1)
    print("docs/en/mkdocs.yml is up to date ✅")