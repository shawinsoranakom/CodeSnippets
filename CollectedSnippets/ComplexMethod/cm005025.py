def save_vocabulary(self, save_directory: str, filename_prefix: str | None = None) -> tuple[str]:
        if not os.path.isdir(save_directory):
            logger.error(f"Vocabulary path ({save_directory}) should be a directory")
            return
        saved_files = []

        if self.separate_vocabs:
            out_src_vocab_file = os.path.join(
                save_directory,
                (filename_prefix + "-" if filename_prefix else "") + VOCAB_FILES_NAMES["vocab"],
            )
            out_tgt_vocab_file = os.path.join(
                save_directory,
                (filename_prefix + "-" if filename_prefix else "") + VOCAB_FILES_NAMES["target_vocab_file"],
            )
            save_json(self.encoder, out_src_vocab_file)
            save_json(self.target_encoder, out_tgt_vocab_file)
            saved_files.append(out_src_vocab_file)
            saved_files.append(out_tgt_vocab_file)
        else:
            out_vocab_file = os.path.join(
                save_directory, (filename_prefix + "-" if filename_prefix else "") + VOCAB_FILES_NAMES["vocab"]
            )
            save_json(self.encoder, out_vocab_file)
            saved_files.append(out_vocab_file)

        for spm_save_filename, spm_orig_path, spm_model in zip(
            [VOCAB_FILES_NAMES["source_spm"], VOCAB_FILES_NAMES["target_spm"]],
            self.spm_files,
            [self.spm_source, self.spm_target],
        ):
            spm_save_path = os.path.join(
                save_directory, (filename_prefix + "-" if filename_prefix else "") + spm_save_filename
            )
            if os.path.abspath(spm_orig_path) != os.path.abspath(spm_save_path) and os.path.isfile(spm_orig_path):
                copyfile(spm_orig_path, spm_save_path)
                saved_files.append(spm_save_path)
            elif not os.path.isfile(spm_orig_path):
                with open(spm_save_path, "wb") as fi:
                    content_spiece_model = spm_model.serialized_model_proto()
                    fi.write(content_spiece_model)
                saved_files.append(spm_save_path)

        return tuple(saved_files)