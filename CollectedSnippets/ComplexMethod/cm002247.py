def ensure_local_index(self) -> None:
        """Ensure index files are available locally, preferring Hub cache snapshots."""
        if self.index_dir is not None and all(
            (self.index_dir / fname).exists() for fname in (EMBEDDINGS_PATH, INDEX_MAP_PATH, TOKENS_PATH)
        ):
            return

        workspace_dir = Path.cwd()
        if all((workspace_dir / fname).exists() for fname in (EMBEDDINGS_PATH, INDEX_MAP_PATH, TOKENS_PATH)):
            self.index_dir = workspace_dir
            return

        logging.info(f"downloading index from hub cache: {self.hub_dataset}")
        snapshot_path = snapshot_download(repo_id=self.hub_dataset, repo_type="dataset")
        snapshot_dir = Path(snapshot_path)
        missing = [
            fname for fname in (EMBEDDINGS_PATH, INDEX_MAP_PATH, TOKENS_PATH) if not (snapshot_dir / fname).exists()
        ]
        if missing:
            raise FileNotFoundError("Missing expected files in Hub snapshot: " + ", ".join(missing))
        self.index_dir = snapshot_dir