def get_gen_models(cache_dir: str | None = None) -> list[dict]:
        """List generative models (LLMs and VLMs) available in the HuggingFace cache.

        Args:
            cache_dir (`str`, *optional*): Path to the HuggingFace cache directory.
                Defaults to the standard cache location.

        Returns:
            `list[dict]`: OpenAI-compatible model list entries with ``id``, ``object``, etc.
        """
        from transformers.models.auto.modeling_auto import (
            MODEL_FOR_CAUSAL_LM_MAPPING_NAMES,
            MODEL_FOR_IMAGE_TEXT_TO_TEXT_MAPPING_NAMES,
            MODEL_FOR_MULTIMODAL_LM_MAPPING_NAMES,
        )

        generative_models = []
        logger.warning("Scanning the cache directory for LLMs and VLMs.")

        for repo in tqdm(scan_cache_dir(cache_dir).repos):
            if repo.repo_type != "model":
                continue

            for ref, revision_info in repo.refs.items():
                config_path = next((f.file_path for f in revision_info.files if f.file_name == "config.json"), None)
                if not config_path:
                    continue

                config = json.loads(config_path.open().read())
                if not (isinstance(config, dict) and "architectures" in config):
                    continue

                architectures = config["architectures"]
                llms = MODEL_FOR_CAUSAL_LM_MAPPING_NAMES.values()
                vlms = MODEL_FOR_IMAGE_TEXT_TO_TEXT_MAPPING_NAMES.values()
                multimodal = MODEL_FOR_MULTIMODAL_LM_MAPPING_NAMES.values()

                if any(arch for arch in architectures if arch in [*llms, *vlms, *multimodal]):
                    author = repo.repo_id.split("/") if "/" in repo.repo_id else ""
                    repo_handle = repo.repo_id + (f"@{ref}" if ref != "main" else "")
                    generative_models.append(
                        {
                            "owned_by": author,
                            "id": repo_handle,
                            "object": "model",
                            "created": repo.last_modified,
                        }
                    )

        return generative_models