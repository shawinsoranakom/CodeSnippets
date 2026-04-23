def _test_model(self, config, inputs, test_image=False, test_text=False):
        model = self.model_class(config).to(torch_device).eval()
        with torch.no_grad():
            result = model(
                input_ids=inputs["input_ids"] if test_text else None,
                attention_mask=inputs["attention_mask"] if test_text else None,
                token_type_ids=inputs["token_type_ids"] if test_text else None,
                pixel_values=inputs["pixel_values"] if test_image else None,
                bool_masked_pos=inputs["bool_masked_pos"] if test_image else None,
            )
        image_size = (self.vision_model_tester.image_size, self.vision_model_tester.image_size)
        patch_size = (self.vision_model_tester.patch_size, self.vision_model_tester.patch_size)
        num_patches = (image_size[1] // patch_size[1]) * (image_size[0] // patch_size[0])

        if test_image:
            self.parent.assertEqual(
                result.image_embeddings.shape,
                (self.vision_model_tester.batch_size, num_patches + 1, self.vision_model_tester.hidden_size),
            )
        else:
            self.parent.assertIsNone(result.image_embeddings)

        if test_text:
            self.parent.assertEqual(
                result.text_embeddings.shape,
                (
                    self.text_model_tester.batch_size,
                    self.text_model_tester.seq_length,
                    self.text_model_tester.hidden_size,
                ),
            )
        else:
            self.parent.assertIsNone(result.text_embeddings)

        if test_image and test_text:
            self.parent.assertEqual(
                result.multimodal_embeddings.shape,
                (
                    self.multimodal_model_tester.batch_size,
                    self.text_model_tester.seq_length + num_patches + 2,
                    self.multimodal_model_tester.hidden_size,
                ),
            )
        else:
            self.parent.assertIsNone(result.multimodal_embeddings)