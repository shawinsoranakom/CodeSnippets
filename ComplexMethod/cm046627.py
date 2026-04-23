def _download_mmproj(
        self,
        *,
        hf_repo: str,
        hf_token: Optional[str] = None,
    ) -> Optional[str]:
        """Download the mmproj (vision projection) file from a GGUF repo.

        Prefers mmproj-F16.gguf, falls back to any mmproj*.gguf file.
        Returns the local path, or None if no mmproj file exists.
        """
        try:
            from huggingface_hub import hf_hub_download, list_repo_files

            files = list_repo_files(hf_repo, token = hf_token)
            mmproj_files = sorted(
                f for f in files if f.endswith(".gguf") and "mmproj" in f.lower()
            )
            if not mmproj_files:
                return None

            # Prefer F16 variant
            target = None
            for f in mmproj_files:
                if "f16" in f.lower():
                    target = f
                    break
            if target is None:
                target = mmproj_files[0]

            logger.info(f"Downloading mmproj: {hf_repo}/{target}")
            local_path = hf_hub_download(
                repo_id = hf_repo,
                filename = target,
                token = hf_token,
            )
            return local_path
        except Exception as e:
            logger.warning(f"Could not download mmproj: {e}")
            return None