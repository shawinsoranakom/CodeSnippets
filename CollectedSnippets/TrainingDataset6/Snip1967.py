def test_gt(runner: CliRunner, root_dir: Path, copy_test_files):
    result = runner.invoke(
        cli,
        ["fix-pages", "docs/lang/docs/doc.md"],
    )
    assert result.exit_code == 1, result.output

    fixed_content = (root_dir / "docs" / "lang" / "docs" / "doc.md").read_text("utf-8")
    expected_content = Path(f"{data_path}/translated_doc_lines_number_gt.md").read_text(
        "utf-8"
    )

    assert fixed_content == expected_content  # Translated doc remains unchanged
    assert "Error processing docs/lang/docs/doc.md" in result.output
    assert (
        "Code block (lines 14-18) has different number of lines than the original block (5 vs 4)"
    ) in result.output