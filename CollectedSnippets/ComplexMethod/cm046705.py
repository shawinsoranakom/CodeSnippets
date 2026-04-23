def without_hf_auth():
    """
    Context manager to temporarily disable HuggingFace authentication.

    Usage:
        with without_hf_auth():
            # Code that should run without cached tokens
            model_info(model_name, token=None)
    """
    # Save environment variables
    saved_env = {}
    env_vars = ["HF_TOKEN", "HUGGINGFACE_HUB_TOKEN", "HF_HOME"]
    for var in env_vars:
        if var in os.environ:
            saved_env[var] = os.environ[var]
            del os.environ[var]

    # Save disable flag
    saved_disable = os.environ.get("HF_HUB_DISABLE_IMPLICIT_TOKEN")
    os.environ["HF_HUB_DISABLE_IMPLICIT_TOKEN"] = "1"

    # Move token files temporarily
    token_files = []
    token_locations = [
        Path.home() / ".cache" / "huggingface" / "token",
        Path.home() / ".huggingface" / "token",
    ]

    for token_loc in token_locations:
        if token_loc.exists():
            temp = tempfile.NamedTemporaryFile(delete = False)
            temp.close()
            shutil.move(str(token_loc), temp.name)
            token_files.append((token_loc, temp.name))

    try:
        yield
    finally:
        # Restore tokens
        for original, temp in token_files:
            try:
                original.parent.mkdir(parents = True, exist_ok = True)
                shutil.move(temp, str(original))
            except Exception as e:
                logger.error(f"Failed to restore token {original}: {e}")

        # Restore environment
        for var, value in saved_env.items():
            os.environ[var] = value

        if saved_disable is not None:
            os.environ["HF_HUB_DISABLE_IMPLICIT_TOKEN"] = saved_disable
        else:
            os.environ.pop("HF_HUB_DISABLE_IMPLICIT_TOKEN", None)