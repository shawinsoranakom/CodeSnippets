def test_batch_call(self):
        # Test 1:
        # default case
        text = ["Hello world!", "Hello world! Longer"]
        expected_tokens = [
            self.ref_tokenizer.instruct_tokenizer.tokenizer.encode(t, bos=True, eos=False) for t in text
        ]
        tokens = self.tokenizer(text)
        self.assertIsInstance(tokens, BatchEncoding)
        self.assertEqual(tokens["input_ids"], expected_tokens)
        self.assertEqual(tokens["attention_mask"], [[1] * len(t) for t in expected_tokens])

        # Test 2:
        # return_attention_mask=False
        tokens = self.tokenizer(text, return_attention_mask=False)
        self.assertEqual(tokens["input_ids"], expected_tokens)
        self.assertNotIn("attention_mask", tokens)

        # Test 3:
        # return_tensors="pt"
        tokens = self.tokenizer(text, return_tensors="pt", padding="longest", return_special_tokens_mask=True)
        self.assertIsInstance(tokens["input_ids"], torch.Tensor)
        self.assertEqual(tokens["input_ids"].shape, torch.Size([2, len(expected_tokens[1])]))
        self.assertTrue(
            torch.equal(
                tokens["input_ids"][0],
                torch.Tensor(
                    (len(expected_tokens[1]) - len(expected_tokens[0]))
                    * [self.ref_tokenizer.instruct_tokenizer.tokenizer.pad_id]
                    + expected_tokens[0]
                ),
            )
        )
        self.assertIsInstance(tokens["attention_mask"], torch.Tensor)
        self.assertEqual(tokens["attention_mask"].shape, torch.Size([2, len(expected_tokens[1])]))
        self.assertTrue(
            torch.equal(
                tokens["attention_mask"][0],
                torch.Tensor(
                    [0] * (len(expected_tokens[1]) - len(expected_tokens[0])) + [1] * len(expected_tokens[0])
                ),
            )
        )
        self.assertTrue(torch.equal(tokens["attention_mask"][1], torch.Tensor([1] * len(expected_tokens[1]))))
        self.assertIsInstance(tokens["special_tokens_mask"], torch.Tensor)
        self.assertEqual(tokens["special_tokens_mask"].shape, torch.Size([2, len(expected_tokens[1])]))
        self.assertTrue(
            torch.equal(
                tokens["special_tokens_mask"][0],
                torch.Tensor(
                    (len(expected_tokens[1]) - len(expected_tokens[0])) * [1]
                    + [1]
                    + [0] * (len(expected_tokens[0]) - 1)
                ),
            )
        )
        self.assertTrue(
            torch.equal(tokens["special_tokens_mask"][1], torch.Tensor([1] + [0] * (len(expected_tokens[1]) - 1)))
        )

        # Test 4:
        # add_special_tokens=False
        expected_tokens = [
            self.ref_tokenizer.instruct_tokenizer.tokenizer.encode(t, bos=False, eos=False) for t in text
        ]
        tokens = self.tokenizer(text, add_special_tokens=False, return_special_tokens_mask=True)
        self.assertIsInstance(tokens, BatchEncoding)
        self.assertEqual(tokens["input_ids"], expected_tokens)
        self.assertEqual(tokens["attention_mask"], [[1] * len(t) for t in expected_tokens])
        self.assertEqual(tokens["special_tokens_mask"], [[0] * len(t) for t in expected_tokens])

        # Test 5:
        # add_special_tokens=True and mode = finetuning
        expected_tokens = [self.ref_tokenizer.instruct_tokenizer.tokenizer.encode(t, bos=True, eos=True) for t in text]
        with patch.object(self.tokenizer, "_mode", ValidationMode.finetuning):
            tokens = self.tokenizer(text, add_special_tokens=True, return_special_tokens_mask=True)
        self.assertIsInstance(tokens, BatchEncoding)
        self.assertEqual(tokens["input_ids"], expected_tokens)
        self.assertEqual(
            tokens["special_tokens_mask"],
            [[1] + [0] * (len(expected_tokens[0]) - 2) + [1], [1] + [0] * (len(expected_tokens[1]) - 2) + [1]],
        )

        # Test 6:
        # empty string in batch
        expected_tokens = [
            self.ref_tokenizer.instruct_tokenizer.tokenizer.encode(t, bos=False, eos=False) for t in text
        ]
        expected_tokens.append([])
        tokens = self.tokenizer(text + [""], add_special_tokens=False, return_special_tokens_mask=True)
        self.assertIsInstance(tokens, BatchEncoding)
        self.assertEqual(tokens["input_ids"], expected_tokens)
        self.assertEqual(tokens["attention_mask"], [[1] * len(t) for t in expected_tokens])
        self.assertEqual(tokens["special_tokens_mask"], [[0] * len(t) for t in expected_tokens])

        # Test 7:
        # empty batch
        tokens = self.tokenizer([""], add_special_tokens=False, return_special_tokens_mask=True)
        self.assertIsInstance(tokens, BatchEncoding)
        self.assertEqual(tokens["input_ids"], [[]])
        self.assertEqual(tokens["attention_mask"], [[]])
        self.assertEqual(tokens["special_tokens_mask"], [[]])