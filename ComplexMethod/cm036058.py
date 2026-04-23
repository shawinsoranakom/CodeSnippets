def test_s3_url_model_tokenizer_paths(mock_pull_files, s3_url):
    """Test that S3 URLs create deterministic local directories for model and
    tokenizer."""
    # Mock pull_files to avoid actually downloading files during tests
    mock_pull_files.return_value = None

    # Create first mock and run the method
    config1 = MockConfig(model=s3_url, tokenizer=s3_url)
    ModelConfig.maybe_pull_model_tokenizer_for_runai(config1, s3_url, s3_url)

    # Check that model and tokenizer point to existing directories
    assert os.path.exists(config1.model), (
        f"Model directory does not exist: {config1.model}"
    )
    assert os.path.isdir(config1.model), (
        f"Model path is not a directory: {config1.model}"
    )
    assert os.path.exists(config1.tokenizer), (
        f"Tokenizer directory does not exist: {config1.tokenizer}"
    )
    assert os.path.isdir(config1.tokenizer), (
        f"Tokenizer path is not a directory: {config1.tokenizer}"
    )

    # Verify that the paths are different from the original S3 URL
    assert config1.model != s3_url, "Model path should be converted to local directory"
    assert config1.tokenizer != s3_url, (
        "Tokenizer path should be converted to local directory"
    )

    # Store the original paths
    created_model_dir = config1.model
    create_tokenizer_dir = config1.tokenizer

    # Create a new mock and run the method with the same S3 URL
    config2 = MockConfig(model=s3_url, tokenizer=s3_url)
    ModelConfig.maybe_pull_model_tokenizer_for_runai(config2, s3_url, s3_url)

    # Check that the new directories exist
    assert os.path.exists(config2.model), (
        f"Model directory does not exist: {config2.model}"
    )
    assert os.path.isdir(config2.model), (
        f"Model path is not a directory: {config2.model}"
    )
    assert os.path.exists(config2.tokenizer), (
        f"Tokenizer directory does not exist: {config2.tokenizer}"
    )
    assert os.path.isdir(config2.tokenizer), (
        f"Tokenizer path is not a directory: {config2.tokenizer}"
    )

    # Verify that the paths are deterministic (same as before)
    assert config2.model == created_model_dir, (
        f"Model paths are not deterministic. "
        f"Original: {created_model_dir}, New: {config2.model}"
    )
    assert config2.tokenizer == create_tokenizer_dir, (
        f"Tokenizer paths are not deterministic. "
        f"Original: {create_tokenizer_dir}, New: {config2.tokenizer}"
    )