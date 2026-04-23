def tokenize_with_weights(self, text:str):
        """Tokenize the text, with weight values - presume 1.0 for all and ignore other features here. The details aren't relevant for a reference impl, and weights themselves has weak effect on SD3."""
        if self.pad_with_end:
            pad_token = self.end_token
        else:
            pad_token = 0
        batch = []
        if self.start_token is not None:
            batch.append((self.start_token, 1.0))
        to_tokenize = text.replace("\n", " ").split(' ')
        to_tokenize = [x for x in to_tokenize if x != ""]
        for word in to_tokenize:
            batch.extend([(t, 1) for t in self.tokenizer(word)["input_ids"][self.tokens_start:-1]])
        batch.append((self.end_token, 1.0))
        if self.pad_to_max_length:
            batch.extend([(pad_token, 1.0)] * (self.max_length - len(batch)))
        if self.min_length is not None and len(batch) < self.min_length:
            batch.extend([(pad_token, 1.0)] * (self.min_length - len(batch)))
        return [batch]