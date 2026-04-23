def save_vocabulary(self, save_directory: str, filename_prefix: str | None = None) -> tuple[str]:
        if os.path.isdir(save_directory):
            if self.subword_tokenizer_type == "sentencepiece":
                vocab_file = os.path.join(
                    save_directory, (filename_prefix + "-" if filename_prefix else "") + VOCAB_FILES_NAMES["spm_file"]
                )
            else:
                vocab_file = os.path.join(
                    save_directory,
                    (filename_prefix + "-" if filename_prefix else "") + VOCAB_FILES_NAMES["vocab_file"],
                )
        else:
            vocab_file = (filename_prefix + "-" if filename_prefix else "") + save_directory

        if self.subword_tokenizer_type == "sentencepiece":
            with open(vocab_file, "wb") as writer:
                content_spiece_model = self.subword_tokenizer.sp_model.serialized_model_proto()
                writer.write(content_spiece_model)
        else:
            with open(vocab_file, "w", encoding="utf-8") as writer:
                index = 0
                for token, token_index in sorted(self.vocab.items(), key=lambda kv: kv[1]):
                    if index != token_index:
                        logger.warning(
                            f"Saving vocabulary to {vocab_file}: vocabulary indices are not consecutive."
                            " Please check that the vocabulary is not corrupted!"
                        )
                        index = token_index
                    writer.write(token + "\n")
                    index += 1
        return (vocab_file,)