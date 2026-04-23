def test_batch_encode_dynamic_overflowing(self):
        """
        When calling batch_encode with multiple sequences, it can return different number of
        overflowing encoding for each sequence:
        [
          Sequence 1: [Encoding 1, Encoding 2],
          Sequence 2: [Encoding 1],
          Sequence 3: [Encoding 1, Encoding 2, ... Encoding N]
        ]
        This needs to be padded so that it can represented as a tensor
        """
        for tokenizer, pretrained_name, kwargs in self.tokenizers_list:
            tokenizer = self.rust_tokenizer_class.from_pretrained(pretrained_name, **kwargs)

            with self.subTest(f"{tokenizer.__class__.__name__} ({pretrained_name}, {tokenizer.__class__.__name__})"):
                returned_tensor = "pt"

                # Single example
                words = ["HuggingFace", "is", "solving", "NLP", "one", "commit", "at", "a", "time"]
                boxes = [[i, i, i, i] for i in range(len(words))]
                tokens = tokenizer.encode_plus(
                    words,
                    boxes=boxes,
                    max_length=6,
                    padding=True,
                    truncation=True,
                    return_tensors=returned_tensor,
                    return_overflowing_tokens=True,
                )

                for key in filter(lambda x: "overflow_to_sample_mapping" not in x, tokens.keys()):
                    if key != "bbox":
                        self.assertEqual(len(tokens[key].shape), 2)
                    else:
                        self.assertEqual(len(tokens[key].shape), 3)

                # Batch of examples
                # For these 2 examples, 3 training examples will be created
                words_batched = [
                    ["HuggingFace", "is", "solving", "NLP", "one", "commit", "at", "a", "time"],
                    ["Very", "tiny", "input"],
                ]
                boxes_batched = [[[i, i, i, i] for i in range(len(words_item))] for words_item in words_batched]
                tokens = tokenizer.batch_encode_plus(
                    words_batched,
                    boxes=boxes_batched,
                    max_length=6,
                    padding=True,
                    truncation="only_first",
                    return_tensors=returned_tensor,
                    return_overflowing_tokens=True,
                )

                for key in filter(lambda x: "overflow_to_sample_mapping" not in x, tokens.keys()):
                    if key != "bbox":
                        self.assertEqual(len(tokens[key].shape), 2)
                        self.assertEqual(tokens[key].shape[-1], 6)
                    else:
                        self.assertEqual(len(tokens[key].shape), 3)
                        self.assertEqual(tokens[key].shape[-1], 4)