def prepare_paths(runner):
    docs_dir = Path("docs")
    en_docs_dir = docs_dir / "en" / "docs"
    lang_docs_dir = docs_dir / "lang" / "docs"
    en_docs_dir.mkdir(parents=True, exist_ok=True)
    lang_docs_dir.mkdir(parents=True, exist_ok=True)
    yield Path.cwd()