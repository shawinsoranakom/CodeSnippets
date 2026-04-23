def new_lang(lang: str = typer.Argument(..., callback=lang_callback)):
    """
    Generate a new docs translation directory for the language LANG.
    """
    new_path: Path = Path("docs") / lang
    if new_path.exists():
        typer.echo(f"The language was already created: {lang}")
        raise typer.Abort()
    new_path.mkdir()
    new_config_path: Path = Path(new_path) / mkdocs_name
    new_config_path.write_text("INHERIT: ../en/mkdocs.yml\n", encoding="utf-8")
    new_llm_prompt_path: Path = new_path / "llm-prompt.md"
    new_llm_prompt_path.write_text("", encoding="utf-8")
    print(f"Successfully initialized: {new_path}")
    update_languages()