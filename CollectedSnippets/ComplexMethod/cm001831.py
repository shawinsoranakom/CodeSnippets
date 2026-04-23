def _check_no_pad_token_padding(self, tokenizer, sequences):
        """Override to handle UdopTokenizer's requirement for boxes parameter"""
        # if tokenizer does not have pad_token_id, an error should be thrown
        if tokenizer.pad_token_id is None:
            with self.assertRaises(ValueError):
                # For UdopTokenizer, we need boxes, so create dummy boxes
                if isinstance(sequences, list) and sequences and isinstance(sequences[0], list):
                    # Batch of sequences
                    boxes = [[[0, 0, 0, 0] for _ in seq] for seq in sequences]
                    tokenizer(sequences, boxes=boxes, padding="longest")
                elif isinstance(sequences, list):
                    # Single sequence (list of words)
                    boxes = [[0, 0, 0, 0] for _ in sequences]
                    tokenizer(sequences, boxes=boxes, padding=True)
                else:
                    # Single string (shouldn't happen for Udop, but handle it)
                    tokenizer(sequences, padding=True)

            # add pad_token_id to pass subsequent tests
            tokenizer.add_special_tokens({"pad_token": "<PAD>"})