def _resolve_hf_checkpoint_dir(self, hf_model_path: str) -> str:
        """Resolve a HF model identifier or local path to a local directory containing checkpoint files.

        - If `hf_model_path` is an existing directory, return it.
        - If it's a file path, return its parent directory.
        - Otherwise treat it as a Hugging Face Hub repo id and download/resolve to the local cache dir.
        """
        if not hf_model_path:
            return hf_model_path

        # Local directory or file path.
        if os.path.isdir(hf_model_path):
            return hf_model_path
        if os.path.isfile(hf_model_path):
            return os.path.dirname(hf_model_path)

        # HuggingFace Hub repo id: snapshot to local cache so we can glob/index files.
        try:
            from huggingface_hub import snapshot_download
        except ImportError as e:
            raise ValueError(
                f"hf_model_path='{hf_model_path}' does not exist locally and huggingface_hub is not available "
                f"to download it. Please provide a local model directory or install huggingface_hub. Error: {e}"
            ) from e

        revision = os.getenv("HF_REVISION")
        offline = os.getenv("HF_HUB_OFFLINE") == "1" or os.getenv("TRANSFORMERS_OFFLINE") == "1"

        # In distributed runs, let rank0 download first to avoid N-way concurrent downloads.
        if torch.distributed.is_available() and torch.distributed.is_initialized():
            if self.rank == 0:
                local_dir = snapshot_download(
                    repo_id=hf_model_path,
                    revision=revision,
                    local_files_only=offline,
                    allow_patterns=[
                        "*.safetensors",
                        "*.bin",
                        "*.index.json",
                        "model.safetensors",
                        "model.safetensors.index.json",
                        "pytorch_model.bin",
                        "pytorch_model.bin.index.json",
                        "config.json",
                    ],
                )
                logger.info(f"Resolved HF repo id '{hf_model_path}' to local dir: {local_dir}")
            torch.distributed.barrier()
            if self.rank != 0:
                local_dir = snapshot_download(
                    repo_id=hf_model_path,
                    revision=revision,
                    local_files_only=True,
                    allow_patterns=[
                        "*.safetensors",
                        "*.bin",
                        "*.index.json",
                        "model.safetensors",
                        "model.safetensors.index.json",
                        "pytorch_model.bin",
                        "pytorch_model.bin.index.json",
                        "config.json",
                    ],
                )
            return local_dir

        local_dir = snapshot_download(
            repo_id=hf_model_path,
            revision=revision,
            local_files_only=offline,
            allow_patterns=[
                "*.safetensors",
                "*.bin",
                "*.index.json",
                "model.safetensors",
                "model.safetensors.index.json",
                "pytorch_model.bin",
                "pytorch_model.bin.index.json",
                "config.json",
            ],
        )
        if self.rank == 0:
            logger.info(f"Resolved HF repo id '{hf_model_path}' to local dir: {local_dir}")
        return local_dir