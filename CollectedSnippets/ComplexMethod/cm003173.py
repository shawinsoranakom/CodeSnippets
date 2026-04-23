def verify_conversion(
    original_model, hf_model, preprocess, image_processor, tokenizer, test_image_path: str | None = None
) -> bool:
    """Verify that the conversion produces the same outputs."""
    print("Verifying conversion...")

    # Create test image
    if test_image_path and os.path.exists(test_image_path):
        image = Image.open(test_image_path)
    else:
        # Create a dummy image
        image = Image.new("RGB", (224, 224), color="red")

    # Verify image processor
    processed_image = preprocess(image).unsqueeze(0)
    pixel_values = image_processor(image, return_tensors="pt").pixel_values
    print("Shape of pixel_values:", pixel_values.shape)
    print("Shape of processed_image:", processed_image.shape)
    assert torch.allclose(pixel_values, processed_image)

    # Use tokenizer to get input_ids
    texts = ["a cat", "a dog", "a bird"]
    token_inputs = tokenizer(texts, return_tensors="pt", padding="max_length", truncation=True, max_length=77)
    input_ids = token_inputs.input_ids

    print(f"Processed text shape: {input_ids.shape}")
    print(f"Processed image shape: {processed_image.shape}")

    with torch.no_grad():
        # Original model outputs
        orig_image_features = original_model.encode_image(processed_image)
        orig_text_features = original_model.encode_text(input_ids)

        # Normalize and compute logits
        orig_image_features = orig_image_features / orig_image_features.norm(dim=-1, keepdim=True)
        orig_text_features = orig_text_features / orig_text_features.norm(dim=-1, keepdim=True)
        orig_logits = original_model.logit_scale.exp() * orig_image_features @ orig_text_features.T

        print(f"Original text features: {orig_text_features[0][:5].tolist()}")
        print(f"Original image features: {orig_image_features[0][:5].tolist()}")

    with torch.no_grad():
        hf_outputs = hf_model(input_ids=input_ids, pixel_values=pixel_values)
        hf_logits = hf_outputs.logits_per_image

        # Debug: Check HF model features
        print(f"HF text features: {hf_outputs.text_embeds[0][:5].tolist()}")
        print(f"HF image features: {hf_outputs.image_embeds[0][:5].tolist()}")
        print(f"HF model EOS token ID: {hf_model.config.text_config.eos_token_id}")

    # Compare outputs
    print(f"Original logits: {orig_logits}")
    print(f"HF logits: {hf_logits}")
    print(f"Logit scale - Original: {original_model.logit_scale.exp():.6f}, HF: {hf_model.logit_scale.exp():.6f}")

    # Check if they're close
    if orig_logits.shape == hf_logits.shape and torch.allclose(orig_logits, hf_logits, atol=1e-4):
        print("[SUCCESS] Conversion verified! Outputs match.")
        return True
    else:
        print("[FAIL] Conversion failed! Outputs don't match.")
        if orig_logits.numel() > 0 and hf_logits.numel() > 0:
            print(f"Max difference: {(orig_logits - hf_logits).abs().max()}")
        return False