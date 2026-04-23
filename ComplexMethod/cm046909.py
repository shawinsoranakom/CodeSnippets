def chunk_data(self, filename = None):
        # Chunks data by max tokens and generation length
        assert filename is not None
        assert os.path.exists(filename)
        assert hasattr(self, "tokenizer")
        if not hasattr(self, "max_seq_length"):
            raise RuntimeError(
                "Please use SynthetidDataKit.from_pretrained(...) first!"
            )
        if not hasattr(self, "overlap") or not hasattr(self, "max_generation_tokens"):
            raise RuntimeError("Please use prepare_qa_generation first!")

        with open(filename, "r", encoding = "utf-8") as f:
            text = f.read()

        max_tokens = (
            self.max_seq_length - self.max_generation_tokens * 2 - 128
        )  # -128 to reduce errors
        if max_tokens <= 5:
            raise RuntimeError("Generation length is way too long!")
        input_ids = self.tokenizer(text, add_special_tokens = False).input_ids

        # Get left and right boundaries
        length = len(input_ids)
        n_chunks = int(np.ceil(length / (max_tokens - self.overlap)))
        boundaries = np.ceil(np.linspace(0, length - self.overlap, n_chunks)).astype(
            int
        )
        boundaries = np.stack((boundaries[:-1], (boundaries + self.overlap)[1:])).T
        boundaries = np.minimum(boundaries, length).tolist()

        # Get extension of filename like .txt
        filename, extension = os.path.splitext(filename)
        if filename.endswith("/"):
            filename = filename[:-1]

        all_filenames = []
        for i, (left, right) in enumerate(boundaries):
            chunked_text = self.tokenizer.decode(input_ids[left:right])
            new_filename = f"{filename}_{i}{extension}"
            all_filenames.append(new_filename)
            with open(new_filename, "w", encoding = "utf-8") as f:
                f.write(chunked_text)
        return all_filenames