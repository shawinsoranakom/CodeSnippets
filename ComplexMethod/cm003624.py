def save_vocabulary(self, save_directory: str, filename_prefix: str | None = None) -> tuple[str]:
        if not os.path.isdir(save_directory):
            logger.error(f"Vocabulary path ({save_directory}) should be a directory")
            return
        out_vocab_file = os.path.join(
            save_directory, (filename_prefix + "-" if filename_prefix else "") + VOCAB_FILES_NAMES["vocab_file"]
        )
        out_monolingual_vocab_file = os.path.join(
            save_directory,
            (filename_prefix + "-" if filename_prefix else "") + VOCAB_FILES_NAMES["monolingual_vocab_file"],
        )

        if os.path.abspath(self.vocab_file) != os.path.abspath(out_vocab_file) and os.path.isfile(self.vocab_file):
            copyfile(self.vocab_file, out_vocab_file)
        elif not os.path.isfile(self.vocab_file):
            with open(out_vocab_file, "wb") as fi:
                content_spiece_model = self.sp_model.serialized_model_proto()
                fi.write(content_spiece_model)

        if os.path.abspath(self.monolingual_vocab_file) != os.path.abspath(
            out_monolingual_vocab_file
        ) and os.path.isfile(self.monolingual_vocab_file):
            copyfile(self.monolingual_vocab_file, out_monolingual_vocab_file)
        elif not os.path.isfile(self.monolingual_vocab_file):
            with open(out_monolingual_vocab_file, "w", encoding="utf-8") as fp:
                for token in self.fairseq_tokens_to_ids:
                    if token not in self.all_special_tokens:
                        fp.write(f"{str(token)} \n")

        return out_vocab_file, out_monolingual_vocab_file