def get_safetensors_params_metadata(
    model: str,
    *,
    revision: str | None = None,
) -> dict[str, Any]:
    """
    Get the safetensors parameters metadata for remote/local model repository.
    """
    full_metadata = {}
    if (model_path := Path(model)).exists():
        safetensors_to_check = model_path.glob("*.safetensors")
        full_metadata = {
            param_name: info
            for file_path in safetensors_to_check
            if file_path.is_file()
            for param_name, info in parse_safetensors_file_metadata(file_path).items()
        }
    else:
        repo_mt = try_get_safetensors_metadata(model, revision=revision)
        if repo_mt and (files_mt := repo_mt.files_metadata):
            full_metadata = {
                param_name: asdict(info)
                for file_mt in files_mt.values()
                for param_name, info in file_mt.tensors.items()
            }
    return full_metadata