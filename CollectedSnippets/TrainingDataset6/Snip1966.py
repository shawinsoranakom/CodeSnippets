def copy_test_files(root_dir: Path, request: pytest.FixtureRequest):
    en_file_path = Path(request.param[0])
    translation_file_path = Path(request.param[1])
    shutil.copy(str(en_file_path), str(root_dir / "docs" / "en" / "docs" / "doc.md"))
    shutil.copy(
        str(translation_file_path), str(root_dir / "docs" / "lang" / "docs" / "doc.md")
    )