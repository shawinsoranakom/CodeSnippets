def test_level_mismatch_2(runner: CliRunner, root_dir: Path, copy_test_files):
    result = runner.invoke(
        cli,
        ["fix-pages", "docs/lang/docs/doc.md"],
    )
    assert result.exit_code == 1

    fixed_content = (root_dir / "docs" / "lang" / "docs" / "doc.md").read_text("utf-8")
    expected_content = Path(
        f"{data_path}/translated_doc_level_mismatch_2.md"
    ).read_text("utf-8")

    assert fixed_content == expected_content  # Translated doc remains unchanged
    assert "Error processing docs/lang/docs/doc.md" in result.output
    assert (
        "Header levels do not match between document and original document"
        " (found ##, expected #) for header №4 in line 13"
    ) in result.output