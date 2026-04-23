def test_fix(runner: CliRunner, root_dir: Path, copy_test_files):
    result = runner.invoke(
        cli,
        ["fix-pages", "docs/lang/docs/doc.md"],
    )
    assert result.exit_code == 0, result.output

    fixed_content = (root_dir / "docs" / "lang" / "docs" / "doc.md").read_text("utf-8")
    expected_content = (data_path / "translated_doc_expected.md").read_text("utf-8")
    assert fixed_content == expected_content

    assert "Fixing multiline code blocks in" in result.output
    assert "Fixing markdown links in" in result.output