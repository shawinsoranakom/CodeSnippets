def _test_model(self, config, inputs, test_image=False, test_text=False):
        model = self.model_class(config).to(torch_device).eval()
        with torch.no_grad():
            result = model(
                input_ids=inputs["input_ids"] if test_text else None,
                input_ids_masked=inputs["input_ids_masked"] if test_text else None,
                attention_mask=inputs["attention_mask"] if test_text else None,
                token_type_ids=inputs["token_type_ids"] if test_text else None,
                pixel_values=inputs["pixel_values"] if test_image else None,
                bool_masked_pos=inputs["bool_masked_pos"] if test_image else None,
                mlm_labels=inputs["mlm_labels"],
                mim_labels=inputs["mim_labels"],
                itm_labels=inputs["itm_labels"],
                return_loss=inputs["return_loss"],
            )
        image_size = (self.vision_model_tester.image_size, self.vision_model_tester.image_size)
        patch_size = (self.vision_model_tester.patch_size, self.vision_model_tester.patch_size)
        num_patches = (image_size[1] // patch_size[1]) * (image_size[0] // patch_size[0])

        if test_image:
            self.parent.assertEqual(
                result.image_embeddings.shape,
                (self.vision_model_tester.batch_size, num_patches + 1, self.vision_model_tester.hidden_size),
            )
            if not test_text:
                self.parent.assertEqual(
                    result.loss_info.mim.dim(),
                    0,
                )
                self.parent.assertEqual(
                    result.mim_logits.shape,
                    (inputs["bool_masked_pos"].sum().item(), self.vision_model_tester.vocab_size),
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
            if not test_image:
                self.parent.assertEqual(result.loss_info.mlm.dim(), 0)
                self.parent.assertEqual(
                    result.mlm_logits.shape,
                    (
                        (inputs["mlm_labels"] != self.multimodal_model_tester.ce_ignore_index).sum().item(),
                        self.text_model_tester.vocab_size,
                    ),
                )
        else:
            self.parent.assertIsNone(result.text_embeddings)

        if test_image and test_text:
            self.parent.assertEqual(
                result.multimodal_masked_embeddings.shape,
                (
                    self.multimodal_model_tester.batch_size,
                    self.text_model_tester.seq_length + num_patches + 2,
                    self.multimodal_model_tester.hidden_size,
                ),
            )
            self.parent.assertEqual(
                result.itm_logits.shape,
                (self.text_model_tester.batch_size, 2),
            )
            self.parent.assertEqual(
                result.mmm_text_logits.shape,
                (
                    (inputs["mlm_labels"] != self.multimodal_model_tester.ce_ignore_index).sum().item(),
                    self.text_model_tester.vocab_size,
                ),
            )
            self.parent.assertEqual(
                result.mmm_image_logits.shape,
                (inputs["bool_masked_pos"].sum().item(), self.vision_model_tester.vocab_size),
            )
            self.parent.assertEqual(
                result.contrastive_logits_per_image.shape,
                (self.vision_model_tester.batch_size, self.text_model_tester.batch_size),
            )
            self.parent.assertEqual(
                result.contrastive_logits_per_text.shape,
                (self.text_model_tester.batch_size, self.vision_model_tester.batch_size),
            )

            for item in [
                result.loss_info.global_contrastive,
                result.loss_info.itm,
                result.loss_info.mmm_text,
                result.loss_info.mmm_image,
            ]:
                self.parent.assertEqual(item.dim(), 0)

            for item in [result.loss_info.mim, result.loss_info.mlm]:
                self.parent.assertIsNone(item)

        else:
            self.parent.assertIsNone(result.multimodal_masked_embeddings)
            for item in [
                result.loss_info.global_contrastive,
                result.loss_info.itm,
                result.loss_info.mmm_text,
                result.loss_info.mmm_image,
            ]:
                self.parent.assertIsNone(item)

        self.parent.assertIsNone(result.multimodal_embeddings)