def _detect_embedding_model(kb_path: Path) -> str:
        """Internal helper to detect the embedding model."""
        metadata_file = kb_path / "embedding_metadata.json"
        if metadata_file.exists():
            try:
                with metadata_file.open("r", encoding="utf-8") as f:
                    metadata = json.load(f)
                    if isinstance(metadata, dict) and "embedding_model" in metadata:
                        model_value = str(metadata.get("embedding_model", "unknown"))
                        if model_value and model_value.lower() != "unknown":
                            return model_value
            except (OSError, json.JSONDecodeError):
                logger.exception("Error reading embedding metadata file '%s'", metadata_file)

        for config_file in kb_path.glob("*.json"):
            if config_file.name == "embedding_metadata.json":
                continue

            try:
                with config_file.open("r", encoding="utf-8") as f:
                    config_data = json.load(f)
                    if not isinstance(config_data, dict):
                        continue

                    model_fields = ["embedding_model", "model", "embedding_model_name", "model_name"]
                    for field in model_fields:
                        if field in config_data:
                            model_value = str(config_data[field])
                            if model_value and model_value.lower() != "unknown":
                                return model_value

                    if "openai" in json.dumps(config_data).lower():
                        openai_models = ["text-embedding-ada-002", "text-embedding-3-small", "text-embedding-3-large"]
                        config_str = json.dumps(config_data).lower()
                        for model in openai_models:
                            if model in config_str:
                                return model

                    if "model" in config_data:
                        model_name = str(config_data["model"])
                        hf_patterns = ["sentence-transformers", "all-MiniLM", "all-mpnet", "multi-qa"]
                        if any(pattern in model_name for pattern in hf_patterns):
                            return model_name

            except (OSError, json.JSONDecodeError):
                logger.exception("Error reading config file '%s'", config_file)
                continue

        return "Unknown"