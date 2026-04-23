def save_vocabulary(self, save_directory: str, filename_prefix: str | None = None) -> tuple[str, ...]:
        """
        Default implementation for common vocabulary saving patterns.
        Saves self.encoder/self.vocab as JSON, optionally with self.bpe_ranks as merges.
        Returns empty tuple if no vocabulary exists.

        Override this method if your tokenizer needs custom saving logic (e.g., SentencePiece models,
        multiple vocabulary files, or special file formats).

        Args:
            save_directory (`str`):
                The directory in which to save the vocabulary.
            filename_prefix (`str`, *optional*):
                An optional prefix to add to the named of the saved files.

        Returns:
            `tuple[str, ...]`: Paths to the files saved, or empty tuple if no files saved.
        """
        import json
        import os

        vocab_attr = getattr(self, "encoder", None) or getattr(self, "vocab", None)
        if vocab_attr is None:
            return ()

        if not os.path.isdir(save_directory):
            logger.error(f"Vocabulary path ({save_directory}) should be a directory")
            return ()

        vocab_files_names = getattr(self, "vocab_files_names", {})
        prefix = f"{filename_prefix}-" if filename_prefix else ""

        # Save vocabulary
        vocab_file = os.path.join(save_directory, prefix + vocab_files_names.get("vocab_file", "vocab.json"))
        with open(vocab_file, "w", encoding="utf-8") as f:
            f.write(json.dumps(vocab_attr, indent=2, sort_keys=True, ensure_ascii=False) + "\n")

        # Save BPE merges if present
        bpe_ranks = getattr(self, "bpe_ranks", None)
        if bpe_ranks is None:
            return (vocab_file,)

        merge_file = os.path.join(save_directory, prefix + vocab_files_names.get("merges_file", "merges.txt"))
        with open(merge_file, "w", encoding="utf-8") as writer:
            if getattr(self, "add_bpe_version_header", False):
                writer.write("#version: 0.2\n")

            index = 0
            for bpe_tokens, token_index in sorted(bpe_ranks.items(), key=lambda kv: kv[1]):
                if index != token_index:
                    logger.warning(
                        f"Saving vocabulary to {merge_file}: BPE merge indices are not consecutive."
                        " Please check that the tokenizer is not corrupted!"
                    )
                    index = token_index
                writer.write(" ".join(bpe_tokens) + "\n")
                index += 1

        return (vocab_file, merge_file)