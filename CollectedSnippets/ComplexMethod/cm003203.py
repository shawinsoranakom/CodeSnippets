def save_vocabulary(self, save_directory: str, filename_prefix: str | None = None) -> tuple[str]:
        if os.path.isdir(save_directory):
            vocab_file = os.path.join(
                save_directory, (filename_prefix + "-" if filename_prefix else "") + VOCAB_FILES_NAMES["vocab_file"]
            )
        else:
            vocab_file = (filename_prefix + "-" if filename_prefix else "") + save_directory
        index = 0
        if " " in self.encoder:
            self.encoder["</_>"] = self.encoder[" "]
            del self.encoder[" "]
        if "\n" in self.encoder:
            self.encoder["</n>"] = self.encoder["\n"]
            del self.encoder["\n"]
        self.encoder = collections.OrderedDict(sorted(self.encoder.items(), key=lambda x: x[1]))
        with open(vocab_file, "w", encoding="utf-8") as writer:
            for token, token_index in self.encoder.items():
                if index != token_index:
                    logger.warning(
                        f"Saving vocabulary to {vocab_file}: vocabulary indices are not consecutive."
                        " Please check that the vocabulary is not corrupted!"
                    )
                    index = token_index
                writer.write(token + "\n")
                index += 1
        return (vocab_file,)