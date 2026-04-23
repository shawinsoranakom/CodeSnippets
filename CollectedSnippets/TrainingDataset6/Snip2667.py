def tmp_file_1(tmp_path: Path) -> Path:
    f = tmp_path / "example1.txt"
    f.write_text("foo")
    return f