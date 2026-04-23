def run_pipeline_test(self, text_generator, _):
        model = text_generator.model
        tokenizer = text_generator.tokenizer

        outputs = text_generator("This is a test")
        self.assertEqual(outputs, [{"generated_text": ANY(str)}])
        self.assertTrue(outputs[0]["generated_text"].startswith("This is a test"))

        outputs = text_generator("This is a test", return_full_text=False)
        self.assertEqual(outputs, [{"generated_text": ANY(str)}])
        self.assertNotIn("This is a test", outputs[0]["generated_text"])

        text_generator = pipeline(
            task="text-generation", model=model, tokenizer=tokenizer, return_full_text=False, max_new_tokens=5
        )
        outputs = text_generator("This is a test")
        self.assertEqual(outputs, [{"generated_text": ANY(str)}])
        self.assertNotIn("This is a test", outputs[0]["generated_text"])

        outputs = text_generator("This is a test", return_full_text=True)
        self.assertEqual(outputs, [{"generated_text": ANY(str)}])
        self.assertTrue(outputs[0]["generated_text"].startswith("This is a test"))

        outputs = text_generator(["This is great !", "Something else"], num_return_sequences=2, do_sample=True)
        self.assertEqual(
            outputs,
            [
                [{"generated_text": ANY(str)}, {"generated_text": ANY(str)}],
                [{"generated_text": ANY(str)}, {"generated_text": ANY(str)}],
            ],
        )

        if text_generator.tokenizer.pad_token is not None:
            outputs = text_generator(
                ["This is great !", "Something else"], num_return_sequences=2, batch_size=2, do_sample=True
            )
            self.assertEqual(
                outputs,
                [
                    [{"generated_text": ANY(str)}, {"generated_text": ANY(str)}],
                    [{"generated_text": ANY(str)}, {"generated_text": ANY(str)}],
                ],
            )

        with self.assertRaises(ValueError):
            outputs = text_generator("test", return_full_text=True, return_text=True)
        with self.assertRaises(ValueError):
            outputs = text_generator("test", return_full_text=True, return_tensors=True)
        with self.assertRaises(ValueError):
            outputs = text_generator("test", return_text=True, return_tensors=True)

        # Empty prompt is slightly special
        # it requires BOS token to exist.
        # Special case for Pegasus which will always append EOS so will
        # work even without BOS.
        if (
            text_generator.tokenizer.bos_token_id is not None
            or "Pegasus" in tokenizer.__class__.__name__
            or "Git" in model.__class__.__name__
        ):
            outputs = text_generator("")
            self.assertEqual(outputs, [{"generated_text": ANY(str)}])
        else:
            with self.assertRaises((ValueError, AssertionError)):
                outputs = text_generator("", add_special_tokens=False)

        # We don't care about infinite range models.
        # They already work.
        # Skip this test for XGLM, since it uses sinusoidal positional embeddings which are resized on-the-fly.
        EXTRA_MODELS_CAN_HANDLE_LONG_INPUTS = [
            "RwkvForCausalLM",
            "XGLMForCausalLM",
            "GPTNeoXForCausalLM",
            "GPTNeoXJapaneseForCausalLM",
            "FuyuForCausalLM",
            "LlamaForCausalLM",
        ]
        if (
            tokenizer.model_max_length < 10000
            and text_generator.model.__class__.__name__ not in EXTRA_MODELS_CAN_HANDLE_LONG_INPUTS
        ):
            # Handling of large generations
            if str(text_generator.device) == "cpu":
                with self.assertRaises((RuntimeError, IndexError, ValueError, AssertionError)):
                    text_generator("This is a test" * 500, max_new_tokens=5)

            outputs = text_generator("This is a test" * 500, handle_long_generation="hole", max_new_tokens=5)
            # Hole strategy cannot work
            if str(text_generator.device) == "cpu":
                with self.assertRaises(ValueError):
                    text_generator(
                        "This is a test" * 500,
                        handle_long_generation="hole",
                        max_new_tokens=tokenizer.model_max_length + 10,
                    )