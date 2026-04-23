def get_embeddings(
        self, sentences: List[str], batch_size=None, bypass_buffer=False
    ):
        """
        Get BERT embeddings for a list of sentences.

        Args:
            sentences (List[str]): A list of text chunks (sentences).

        Returns:
            NumPy array of embeddings.
        """
        # if self.buffer_embeddings.any() and not bypass_buffer:
        #     return self.buffer_embeddings

        if self.device.type in ["cpu", "gpu", "cuda", "mps"]:
            import torch

            # Tokenize sentences and convert to tensor
            if batch_size is None:
                batch_size = self.default_batch_size

            all_embeddings = []
            for i in range(0, len(sentences), batch_size):
                batch_sentences = sentences[i : i + batch_size]
                encoded_input = self.tokenizer(
                    batch_sentences, padding=True, truncation=True, return_tensors="pt"
                )
                encoded_input = {
                    key: tensor.to(self.device) for key, tensor in encoded_input.items()
                }

                # Ensure no gradients are calculated
                with torch.no_grad():
                    model_output = self.model(**encoded_input)

                # Get embeddings from the last hidden state (mean pooling)
                embeddings = model_output.last_hidden_state.mean(dim=1).cpu().numpy()
                all_embeddings.append(embeddings)

            self.buffer_embeddings = np.vstack(all_embeddings)
        elif self.device.type == "cpu":
            # self.buffer_embeddings = self.model(sentences)
            if batch_size is None:
                batch_size = self.default_batch_size

            all_embeddings = []
            for i in range(0, len(sentences), batch_size):
                batch_sentences = sentences[i : i + batch_size]
                embeddings = self.model(batch_sentences)
                all_embeddings.append(embeddings)

            self.buffer_embeddings = np.vstack(all_embeddings)
        return self.buffer_embeddings