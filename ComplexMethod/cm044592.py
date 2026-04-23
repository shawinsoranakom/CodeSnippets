def test_wrap_file() -> None:
    fd, filename = tempfile.mkstemp()
    with os.fdopen(fd, "wb") as f:
        total = f.write(b"Hello, World!")
    try:
        with open(filename, "rb") as file:
            with rich.progress.wrap_file(file, total=total) as f:
                assert f.read() == b"Hello, World!"
                assert f.mode == "rb"
                assert f.name == filename
            assert f.closed
            assert not f.handle.closed
            assert not file.closed
        assert file.closed
    finally:
        os.remove(filename)