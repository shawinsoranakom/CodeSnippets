def test_batch_encode_dynamic_overflowing(self):
        """
        When calling batch_encode with multiple sequence it can returns different number of
        overflowing encoding for each sequence:
        [
          Sequence 1: [Encoding 1, Encoding 2],
          Sequence 2: [Encoding 1],
          Sequence 3: [Encoding 1, Encoding 2, ... Encoding N]
        ]
        This needs to be padded so that it can represented as a tensor
        """
        for tokenizer, pretrained_name, kwargs in self.tokenizers_list:
            tokenizer = self.get_tokenizer(pretrained_name, **kwargs)

            with self.subTest(f"{tokenizer.__class__.__name__} ({pretrained_name})"):
                if is_torch_available():
                    returned_tensor = "pt"
                else:
                    self.skipTest(reason="No expected framework (PT) found")

                if not tokenizer.pad_token or tokenizer.pad_token_id < 0:
                    self.skipTest(reason="This tokenizer has no padding token set, or pad_token_id < 0")

                tokens = tokenizer(
                    "HuggingFace is solving NLP one commit at a time",
                    max_length=6,
                    padding=True,
                    truncation=True,
                    return_tensors=returned_tensor,
                    return_overflowing_tokens=True,
                )

                for key in filter(lambda x: "overflow_to_sample_mapping" not in x, tokens.keys()):
                    self.assertEqual(len(tokens[key].shape), 2)

                # Mono sample
                tokens = tokenizer(
                    ["HuggingFace is solving NLP one commit at a time"],
                    max_length=6,
                    padding=True,
                    truncation="only_first",
                    return_tensors=returned_tensor,
                    return_overflowing_tokens=True,
                )

                for key in filter(lambda x: "overflow_to_sample_mapping" not in x, tokens.keys()):
                    self.assertEqual(len(tokens[key].shape), 2)
                    self.assertEqual(tokens[key].shape[-1], 6)

                # Multi sample
                tokens = tokenizer(
                    ["HuggingFace is solving NLP one commit at a time", "Very tiny input"],
                    max_length=6,
                    padding=True,
                    truncation="only_first",
                    return_tensors=returned_tensor,
                    return_overflowing_tokens=True,
                )

                for key in filter(lambda x: "overflow_to_sample_mapping" not in x, tokens.keys()):
                    self.assertEqual(len(tokens[key].shape), 2)
                    self.assertEqual(tokens[key].shape[-1], 6)