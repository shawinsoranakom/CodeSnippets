def live(
    lang: str = typer.Argument(
        None, callback=lang_callback, autocompletion=complete_existing_lang
    ),
    dirty: bool = False,
) -> None:
    """
    Serve with livereload a docs site for a specific language.

    This only shows the actual translated files, not the placeholders created with
    build-all.

    Takes an optional LANG argument with the name of the language to serve, by default
    en.
    """
    # Enable line numbers during local development to make it easier to highlight
    if lang is None:
        lang = "en"
    lang_path: Path = docs_path / lang
    # Enable line numbers during local development to make it easier to highlight
    args = ["mkdocs", "serve", "--dev-addr", "127.0.0.1:8008"]
    if dirty:
        args.append("--dirty")
    subprocess.run(
        args, env={**os.environ, "LINENUMS": "true"}, cwd=lang_path, check=True
    )