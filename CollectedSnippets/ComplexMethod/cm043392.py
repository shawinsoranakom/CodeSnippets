async def generate_index_files(
        self, force_generate_facts: bool = False, clear_bm25_cache: bool = False
    ) -> None:
        """
        Generate index files for all documents in parallel batches

        Args:
            force_generate_facts (bool): If True, regenerate indexes even if they exist
            clear_bm25_cache (bool): If True, clear existing BM25 index cache
        """
        self.logger.info("Starting index generation for documentation files.")

        md_files = [
            self.docs_dir / f
            for f in os.listdir(self.docs_dir)
            if f.endswith(".md") and not any(f.endswith(x) for x in [".q.md", ".xs.md"])
        ]

        # Filter out files that already have .q files unless force=True
        if not force_generate_facts:
            md_files = [
                f
                for f in md_files
                if not (self.docs_dir / f.name.replace(".md", ".q.md")).exists()
            ]

        if not md_files:
            self.logger.info("All index files exist. Use force=True to regenerate.")
        else:
            # Process documents in batches
            for i in range(0, len(md_files), self.batch_size):
                batch = md_files[i : i + self.batch_size]
                self.logger.info(
                    f"Processing batch {i//self.batch_size + 1}/{(len(md_files)//self.batch_size) + 1}"
                )
                await self._process_document_batch(batch)

        self.logger.info("Index generation complete, building/updating search index.")
        self.build_search_index(clear_cache=clear_bm25_cache)