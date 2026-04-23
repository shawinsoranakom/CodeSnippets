def save_vocabulary(self, save_directory: str, filename_prefix: str | None = None) -> tuple[str]:
        index = 0
        if os.path.isdir(save_directory):
            vocab_file = os.path.join(
                save_directory, (filename_prefix + "-" if filename_prefix else "") + VOCAB_FILES_NAMES["vocab_file"]
            )
            emoji_file = os.path.join(
                save_directory, (filename_prefix + "-" if filename_prefix else "") + VOCAB_FILES_NAMES["emoji_file"]
            )
        else:
            vocab_file = (
                (filename_prefix + "-" if filename_prefix else "") + save_directory + VOCAB_FILES_NAMES["vocab_file"]
            )
            emoji_file = (
                (filename_prefix + "-" if filename_prefix else "") + save_directory + VOCAB_FILES_NAMES["emoji_file"]
            )
        with open(vocab_file, "w", encoding="utf-8") as writer:
            for token_index, token in self.ids_to_tokens.items():
                if index != token_index:
                    logger.warning(
                        f"Saving vocabulary to {vocab_file}: vocabulary indices are not consecutive."
                        " Please check that the vocabulary is not corrupted!"
                    )
                    index = token_index
                writer.write(",".join(token) + "\n")
                index += 1
        with open(emoji_file, "w", encoding="utf-8") as writer:
            json.dump(self.emoji, writer)
        return vocab_file, emoji_file