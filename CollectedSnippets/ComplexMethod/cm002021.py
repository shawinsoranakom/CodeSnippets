def _test_apply_chat_template(
        self,
        modality: str,
        batch_size: int,
        return_tensors: str,
        input_name: str,
        processor_name: str,
        input_data: list[str],
    ):
        if return_tensors != "pt":
            self.skipTest("CSM only supports PyTorch tensors")
        processor = self.get_processor()
        if processor.chat_template is None:
            self.skipTest("Processor has no chat template")

        if processor_name not in self.processor_class.get_attributes():
            self.skipTest(f"{processor_name} attribute not present in {self.processor_class}")

        # some models have only Fast image processor
        if getattr(processor, processor_name).__class__.__name__.endswith("Fast"):
            return_tensors = "pt"

        batch_messages = [
            [
                {
                    "role": "0",
                    "content": [{"type": "text", "text": "Describe this."}],
                },
            ]
        ] * batch_size

        # Test that jinja can be applied
        formatted_prompt = processor.apply_chat_template(batch_messages, add_generation_prompt=True, tokenize=False)
        self.assertEqual(len(formatted_prompt), batch_size)

        # Test that tokenizing with template and directly with `self.tokenizer` gives same output
        formatted_prompt_tokenized = processor.apply_chat_template(
            batch_messages, add_generation_prompt=True, tokenize=True, return_tensors=return_tensors
        )
        add_special_tokens = True
        if processor.tokenizer.bos_token is not None and formatted_prompt[0].startswith(processor.tokenizer.bos_token):
            add_special_tokens = False
        tok_output = processor.tokenizer(
            formatted_prompt, return_tensors=return_tensors, add_special_tokens=add_special_tokens
        )
        expected_output = tok_output.input_ids
        self.assertListEqual(expected_output.tolist(), formatted_prompt_tokenized.tolist())

        # Test that kwargs passed to processor's `__call__` are actually used
        tokenized_prompt_100 = processor.apply_chat_template(
            batch_messages,
            add_generation_prompt=True,
            tokenize=True,
            padding="max_length",
            truncation=True,
            return_tensors=return_tensors,
            max_length=100,
        )
        self.assertEqual(len(tokenized_prompt_100[0]), 100)

        # Test that `return_dict=True` returns text related inputs in the dict
        out_dict_text = processor.apply_chat_template(
            batch_messages,
            add_generation_prompt=True,
            tokenize=True,
            return_dict=True,
            return_tensors=return_tensors,
        )
        self.assertTrue(all(key in out_dict_text for key in ["input_ids", "attention_mask"]))
        self.assertEqual(len(out_dict_text["input_ids"]), batch_size)
        self.assertEqual(len(out_dict_text["attention_mask"]), batch_size)

        # Test that with modality URLs and `return_dict=True`, we get modality inputs in the dict
        for idx, url in enumerate(input_data[:batch_size]):
            batch_messages[idx][0]["content"] = [batch_messages[idx][0]["content"][0], {"type": modality, "url": url}]

        out_dict = processor.apply_chat_template(
            batch_messages,
            add_generation_prompt=True,
            tokenize=True,
            return_dict=True,
            return_tensors=return_tensors,
            num_frames=2,  # by default no more than 2 frames, otherwise too slow
        )
        input_name = getattr(self, input_name)
        print(f"================ input_name={input_name} =================")
        print(f"out_dict={out_dict.keys()}")
        self.assertTrue(input_name in out_dict)
        self.assertEqual(len(out_dict["input_ids"]), batch_size)
        self.assertEqual(len(out_dict["attention_mask"]), batch_size)
        self.assertEqual(len(out_dict[input_name]), batch_size)

        return_tensor_to_type = {"pt": torch.Tensor, "np": np.ndarray, None: list}
        for k in out_dict:
            self.assertIsInstance(out_dict[k], return_tensor_to_type[return_tensors])

        # Test continue from final message
        assistant_message = {
            "role": "1",
            "content": [{"type": "text", "text": "It is the sound of"}],
        }
        for idx, url in enumerate(input_data[:batch_size]):
            batch_messages[idx] = batch_messages[idx] + [assistant_message]
        continue_prompt = processor.apply_chat_template(batch_messages, continue_final_message=True, tokenize=False)
        for prompt in continue_prompt:
            self.assertTrue(prompt.endswith("It is the sound of"))