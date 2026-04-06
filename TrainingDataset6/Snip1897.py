def generate_readme() -> None:
    """
    Generate README.md content from main index.md
    """
    readme_path = Path("README.md")
    old_content = readme_path.read_text("utf-8")
    new_content = generate_readme_content()
    if new_content != old_content:
        print("README.md outdated from the latest index.md")
        print("Updating README.md")
        readme_path.write_text(new_content, encoding="utf-8")
        raise typer.Exit(1)
    print("README.md is up to date ✅")