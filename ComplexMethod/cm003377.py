def test(
    original_model,
    our_model: Mask2FormerForUniversalSegmentation,
    image_processor: Mask2FormerImageProcessor,
    tolerance: float,
):
    with torch.no_grad():
        original_model = original_model.eval()
        our_model = our_model.eval()

        im = prepare_img()
        x = image_processor(images=im, return_tensors="pt")["pixel_values"]

        original_model_backbone_features = original_model.backbone(x.clone())
        our_model_output: Mask2FormerModelOutput = our_model.model(x.clone(), output_hidden_states=True)

        # Test backbone
        for original_model_feature, our_model_feature in zip(
            original_model_backbone_features.values(), our_model_output.encoder_hidden_states
        ):
            assert torch.allclose(original_model_feature, our_model_feature, atol=tolerance), (
                "The backbone features are not the same."
            )

        # Test pixel decoder
        mask_features, _, multi_scale_features = original_model.sem_seg_head.pixel_decoder.forward_features(
            original_model_backbone_features
        )

        for original_model_feature, our_model_feature in zip(
            multi_scale_features, our_model_output.pixel_decoder_hidden_states
        ):
            assert torch.allclose(original_model_feature, our_model_feature, atol=tolerance), (
                "The pixel decoder feature are not the same"
            )

        # Let's test the full model
        tr_complete = T.Compose(
            [T.Resize((384, 384)), T.ToTensor()],
        )
        y = (tr_complete(im) * 255.0).to(torch.int).float()

        # modify original Mask2Former code to return mask and class logits
        original_class_logits, original_mask_logits = original_model([{"image": y.clone().squeeze(0)}])

        our_model_out: Mask2FormerForUniversalSegmentationOutput = our_model(x.clone())
        our_mask_logits = our_model_out.masks_queries_logits
        our_class_logits = our_model_out.class_queries_logits

        assert original_mask_logits.shape == our_mask_logits.shape, "Output masks shapes are not matching."
        assert original_class_logits.shape == our_class_logits.shape, "Output class logits shapes are not matching."
        assert torch.allclose(original_class_logits, our_class_logits, atol=tolerance), (
            "The class logits are not the same."
        )
        assert torch.allclose(original_mask_logits, our_mask_logits, atol=tolerance), (
            "The predicted masks are not the same."
        )

        logger.info("Test passed!")