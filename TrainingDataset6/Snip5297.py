def client():
    static_dir: Path = Path(os.getcwd()) / "static"
    static_dir.mkdir(exist_ok=True)
    sample_file = static_dir / "sample.txt"
    sample_file.write_text("This is a sample static file.")
    from docs_src.static_files.tutorial001_py310 import app

    with TestClient(app) as client:
        yield client
    sample_file.unlink()
    static_dir.rmdir()