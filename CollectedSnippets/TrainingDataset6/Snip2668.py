def tmp_file_2(tmp_path: Path) -> Path:
    f = tmp_path / "example2.txt"
    f.write_text("bar")
    return f