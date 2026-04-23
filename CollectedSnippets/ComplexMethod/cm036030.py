def sample(self):
        """
        ### Sampling function to generate samples periodically while training
        """

        # Empty tensor for data filled with `[PAD]`.
        data = torch.full((self.seq_len, len(self.prompt)), self.padding_token, dtype=torch.long)
        # Add the prompts one by one
        for i, p in enumerate(self.prompt):
            # Get token indexes
            d = self.text.text_to_i(p)
            # Add to the tensor
            s = min(self.seq_len, len(d))
            data[:s, i] = d[:s]
        # Move the tensor to current device
        data = data.to(self.device)

        # Get masked input and labels
        data, labels = self.mlm(data)
        # Get model outputs
        output, *_ = self.model(data)

        # Print the samples generated
        for j in range(data.shape[1]):
            # Collect output from printing
            log = []
            # For each token
            for i in range(len(data)):
                # If the label is not `[PAD]`
                if labels[i, j] != self.padding_token:
                    # Get the prediction
                    t = output[i, j].argmax().item()
                    # If it's a printable character
                    if t < len(self.text.itos):
                        # Correct prediction
                        if t == labels[i, j]:
                            log.append((self.text.itos[t], Text.value))
                        # Incorrect prediction
                        else:
                            log.append((self.text.itos[t], Text.danger))
                    # If it's not a printable character
                    else:
                        log.append(('*', Text.danger))
                # If the label is `[PAD]` (unmasked) print the original.
                elif data[i, j] < len(self.text.itos):
                    log.append((self.text.itos[data[i, j]], Text.subtle))

            # Print
            logger.log(log)