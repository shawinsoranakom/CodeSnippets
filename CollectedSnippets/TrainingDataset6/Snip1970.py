def test_not_translated(runner: CliRunner, root_dir: Path, copy_test_files):
    result = runner.invoke(
        cli,
        ["fix-pages", "docs/lang/docs/doc.md"],
    )
    assert result.exit_code == 0, result.output

    fixed_content = (root_dir / "docs" / "lang" / "docs" / "doc.md").read_text("utf-8")
    expected_content = Path(
        f"{data_path}/translated_doc_mermaid_not_translated.md"
    ).read_text("utf-8")

    assert fixed_content == expected_content  # Translated doc remains unchanged
    assert ("Skipping mermaid code block replacement") not in result.output