def build_search_index(self, clear_cache=False) -> None:
        """
        Checks for new or modified .q.md files by comparing file-hash.
        If none need reindexing and clear_cache is False, loads existing index if available.
        Otherwise, reindexes only changed/new files and merges or creates a new index.
        """
        # If clear_cache is True, we skip partial logic: rebuild everything from scratch
        if clear_cache:
            self.logger.info("Clearing cache and rebuilding full search index.")
            if self.bm25_index_file.exists():
                self.bm25_index_file.unlink()

        process = psutil.Process()
        self.logger.info("Checking which .q.md files need (re)indexing...")

        # Gather all .q.md files
        q_files = [
            self.docs_dir / f for f in os.listdir(self.docs_dir) if f.endswith(".q.md")
        ]

        # We'll store known (unchanged) facts in these lists
        existing_facts: List[str] = []
        existing_tokens: List[List[str]] = []

        # Keep track of invalid lines for logging
        invalid_lines = []
        needSet = []  # files that must be (re)indexed

        for qf in q_files:
            token_cache_file = qf.with_suffix(".q.tokens")

            # If no .q.tokens or clear_cache is True → definitely reindex
            if clear_cache or not token_cache_file.exists():
                needSet.append(qf)
                continue

            # Otherwise, load the existing cache and compare hash
            cache = self._load_or_create_token_cache(qf)
            # If the .q.tokens was out of date (i.e. changed hash), we reindex
            if len(cache["facts"]) == 0 or cache.get(
                "content_hash"
            ) != _compute_file_hash(qf):
                needSet.append(qf)
            else:
                # File is unchanged → retrieve cached token data
                for line, cache_data in cache["facts"].items():
                    existing_facts.append(line)
                    existing_tokens.append(cache_data["tokens"])
                    self.document_map[line] = qf  # track the doc for that fact

        if not needSet and not clear_cache:
            # If no file needs reindexing, try loading existing index
            if self.maybe_load_bm25_index(clear_cache=False):
                self.logger.info(
                    "No new/changed .q.md files found. Using existing BM25 index."
                )
                return
            else:
                # If there's no existing index, we must build a fresh index from the old caches
                self.logger.info(
                    "No existing BM25 index found. Building from cached facts."
                )
                if existing_facts:
                    self.logger.info(
                        f"Building BM25 index with {len(existing_facts)} cached facts."
                    )
                    self.bm25_index = BM25Okapi(existing_tokens)
                    self.tokenized_facts = existing_facts
                    with open(self.bm25_index_file, "wb") as f:
                        pickle.dump(
                            {
                                "bm25_index": self.bm25_index,
                                "tokenized_facts": self.tokenized_facts,
                            },
                            f,
                        )
                else:
                    self.logger.warning("No facts found at all. Index remains empty.")
                return

        # ----------------------------------------------------- /Users/unclecode/.crawl4ai/docs/14_proxy_security.q.q.tokens '/Users/unclecode/.crawl4ai/docs/14_proxy_security.q.md'
        # If we reach here, we have new or changed .q.md files
        # We'll parse them, reindex them, and then combine with existing_facts
        # -----------------------------------------------------

        self.logger.info(f"{len(needSet)} file(s) need reindexing. Parsing now...")

        # 1) Parse the new or changed .q.md files
        new_facts = []
        new_tokens = []
        with tqdm(total=len(needSet), desc="Indexing changed files") as file_pbar:
            for file in needSet:
                # We'll build up a fresh cache
                fresh_cache = {"facts": {}, "content_hash": _compute_file_hash(file)}
                try:
                    with open(file, "r", encoding="utf-8") as f_obj:
                        content = f_obj.read().strip()
                        lines = [l.strip() for l in content.split("\n") if l.strip()]

                    for line in lines:
                        is_valid, error = self._validate_fact_line(line)
                        if not is_valid:
                            invalid_lines.append((file, line, error))
                            continue

                        tokens = self.preprocess_text(line)
                        fresh_cache["facts"][line] = {
                            "tokens": tokens,
                            "added": time.time(),
                        }
                        new_facts.append(line)
                        new_tokens.append(tokens)
                        self.document_map[line] = file

                    # Save the new .q.tokens with updated hash
                    self._save_token_cache(file, fresh_cache)

                    mem_usage = process.memory_info().rss / 1024 / 1024
                    self.logger.debug(
                        f"Memory usage after {file.name}: {mem_usage:.2f}MB"
                    )

                except Exception as e:
                    self.logger.error(f"Error processing {file}: {str(e)}")

                file_pbar.update(1)

        if invalid_lines:
            self.logger.warning(f"Found {len(invalid_lines)} invalid fact lines:")
            for file, line, error in invalid_lines:
                self.logger.warning(f"{file}: {error} in line: {line[:50]}...")

        # 2) Merge newly tokenized facts with the existing ones
        all_facts = existing_facts + new_facts
        all_tokens = existing_tokens + new_tokens

        # 3) Build BM25 index from combined facts
        self.logger.info(
            f"Building BM25 index with {len(all_facts)} total facts (old + new)."
        )
        self.bm25_index = BM25Okapi(all_tokens)
        self.tokenized_facts = all_facts

        # 4) Save the updated BM25 index to disk
        with open(self.bm25_index_file, "wb") as f:
            pickle.dump(
                {
                    "bm25_index": self.bm25_index,
                    "tokenized_facts": self.tokenized_facts,
                },
                f,
            )

        final_mem = process.memory_info().rss / 1024 / 1024
        self.logger.info(f"Search index updated. Final memory usage: {final_mem:.2f}MB")