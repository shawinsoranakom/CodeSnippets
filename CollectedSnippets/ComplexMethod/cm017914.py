def test_output_to_file_with_data_uris(shared_tmp_dir, test_vector) -> None:
    """Test CLI functionality when keep_data_uris is enabled"""

    output_file = os.path.join(shared_tmp_dir, test_vector.filename + ".output")
    result = subprocess.run(
        [
            "python",
            "-m",
            "markitdown",
            "--keep-data-uris",
            "-o",
            output_file,
            os.path.join(TEST_FILES_DIR, test_vector.filename),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"CLI exited with error: {result.stderr}"
    assert os.path.exists(output_file), f"Output file not created: {output_file}"

    with open(output_file, "r") as f:
        output_data = f.read()
        for test_string in test_vector.must_include:
            assert test_string in output_data
        for test_string in test_vector.must_not_include:
            assert test_string not in output_data

    os.remove(output_file)
    assert not os.path.exists(output_file), f"Output file not deleted: {output_file}"