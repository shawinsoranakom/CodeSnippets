def test_fastapi_cli():
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "coverage",
            "run",
            "-m",
            "fastapi",
            "dev",
            "non_existent_file.py",
        ],
        capture_output=True,
        encoding="utf-8",
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )
    assert result.returncode == 1, result.stdout
    assert "Path does not exist non_existent_file.py" in result.stdout