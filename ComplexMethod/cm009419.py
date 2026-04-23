def refresh(provider: str, data_dir: Path) -> None:  # noqa: C901, PLR0915
    """Download and merge model profile data for a specific provider.

    Args:
        provider: Provider ID from models.dev (e.g., `'anthropic'`, `'openai'`).
        data_dir: Directory containing `profile_augmentations.toml` and where
            `profiles.py` will be written.
    """
    # Validate and canonicalize data directory path
    data_dir = _validate_data_dir(data_dir)

    api_url = "https://models.dev/api.json"

    print(f"Provider: {provider}")
    print(f"Data directory: {data_dir}")
    print()

    # Download data from models.dev
    print(f"Downloading data from {api_url}...")
    try:
        response = httpx.get(api_url, timeout=30)
        response.raise_for_status()
    except httpx.TimeoutException:
        msg = f"Request timed out connecting to {api_url}"
        print(f"❌ {msg}", file=sys.stderr)
        sys.exit(1)
    except httpx.HTTPStatusError as e:
        msg = f"HTTP error {e.response.status_code} from {api_url}"
        print(f"❌ {msg}", file=sys.stderr)
        sys.exit(1)
    except httpx.RequestError as e:
        msg = f"Failed to connect to {api_url}: {e}"
        print(f"❌ {msg}", file=sys.stderr)
        sys.exit(1)

    try:
        all_data = response.json()
    except json.JSONDecodeError as e:
        msg = f"Invalid JSON response from API: {e}"
        print(f"❌ {msg}", file=sys.stderr)
        sys.exit(1)

    # Basic validation
    if not isinstance(all_data, dict):
        msg = "Expected API response to be a dictionary"
        print(f"❌ {msg}", file=sys.stderr)
        sys.exit(1)

    provider_count = len(all_data)
    model_count = sum(len(p.get("models", {})) for p in all_data.values())
    print(f"Downloaded {provider_count} providers with {model_count} models")

    # Extract data for this provider
    if provider not in all_data:
        msg = f"Provider '{provider}' not found in models.dev data"
        print(msg, file=sys.stderr)
        sys.exit(1)

    provider_data = all_data[provider]
    models = provider_data.get("models", {})
    print(f"Extracted {len(models)} models for {provider}")

    # Load augmentations
    print("Loading augmentations...")
    provider_aug, model_augs = _load_augmentations(data_dir)

    # Merge and convert to profiles
    profiles: dict[str, dict[str, Any]] = {}
    for model_id, model_data in models.items():
        base_profile = _model_data_to_profile(model_data)
        profiles[model_id] = _apply_overrides(
            base_profile, provider_aug, model_augs.get(model_id)
        )

    # Include new models defined purely via augmentations
    extra_models = set(model_augs) - set(models)
    if extra_models:
        print(f"Adding {len(extra_models)} models from augmentations only...")
    for model_id in sorted(extra_models):
        profiles[model_id] = _apply_overrides({}, provider_aug, model_augs[model_id])

    _warn_undeclared_profile_keys(profiles)

    # Ensure directory exists
    try:
        data_dir.mkdir(parents=True, exist_ok=True, mode=0o755)
    except PermissionError:
        msg = f"Permission denied creating directory: {data_dir}"
        print(f"❌ {msg}", file=sys.stderr)
        sys.exit(1)
    except OSError as e:
        msg = f"Failed to create directory: {e}"
        print(f"❌ {msg}", file=sys.stderr)
        sys.exit(1)

    # Write as Python module
    output_file = data_dir / "_profiles.py"
    print(f"Writing to {output_file}...")
    module_content = [f'"""{MODULE_ADMONITION}"""\n\n', "from typing import Any\n\n"]
    module_content.append("_PROFILES: dict[str, dict[str, Any]] = ")
    json_str = json.dumps(dict(sorted(profiles.items())), indent=4)
    json_str = (
        json_str.replace("true", "True")
        .replace("false", "False")
        .replace("null", "None")
    )
    # Add trailing commas for ruff format compliance
    json_str = re.sub(r"([^\s,{\[])(?=\n\s*[\}\]])", r"\1,", json_str)
    module_content.append(f"{json_str}\n")
    _write_profiles_file(output_file, "".join(module_content))

    print(
        f"✓ Successfully refreshed {len(profiles)} model profiles "
        f"({output_file.stat().st_size:,} bytes)"
    )