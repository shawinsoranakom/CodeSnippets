def convert_blip2_checkpoint(
    model_name, pytorch_dump_folder_path=None, push_to_hub=False, lavis_device="cpu", hf_model_device="cpu"
):
    """
    Copy/paste/tweak model's weights to Transformers design.
    """
    if "opt" in model_name:
        tokenizer = AutoTokenizer.from_pretrained("facebook/opt-2.7b")
    elif "itm" in model_name:
        tokenizer = BertTokenizer.from_pretrained("bert-base-uncased", truncation_side="right")
        tokenizer.add_special_tokens({"bos_token": "[DEC]"})
    else:
        tokenizer = AutoTokenizer.from_pretrained("google/flan-t5-xl")

    if "itm" in model_name:
        eos_token_id = None
    else:
        eos_token_id = tokenizer("\n", add_special_tokens=False).input_ids[0]
    config, image_size = get_blip2_config(model_name, eos_token_id=eos_token_id)

    if "itm" in model_name:
        hf_model = Blip2ForImageTextRetrieval(config).eval()
    else:
        hf_model = Blip2ForConditionalGeneration(config).eval()

    model_name_to_original = {
        "blip2-opt-2.7b": ("blip2_opt", "pretrain_opt2.7b"),
        "blip2-opt-6.7b": ("blip2_opt", "pretrain_opt6.7b"),
        "blip2-opt-2.7b-coco": ("blip2_opt", "caption_coco_opt2.7b"),
        "blip2-opt-6.7b-coco": ("blip2_opt", "caption_coco_opt6.7b"),
        "blip2-flan-t5-xl": ("blip2_t5", "pretrain_flant5xl"),
        "blip2-flan-t5-xl-coco": ("blip2_t5", "caption_coco_flant5xl"),
        "blip2-flan-t5-xxl": ("blip2_t5", "pretrain_flant5xxl"),
        "blip2-itm-vit-g": ("blip2_image_text_matching", "pretrain"),
        "blip2-itm-vit-g-coco": ("blip2_image_text_matching", "coco"),
    }

    name, type = model_name_to_original[model_name]

    # load original model
    print("Loading original model...")
    original_model, vis_processors, _ = load_model_and_preprocess(
        name=name, model_type=type, is_eval=True, device=lavis_device
    )
    original_model.eval()
    print("Done!")

    # update state dict keys
    state_dict = original_model.state_dict()
    rename_keys = create_rename_keys(config, model_name)
    for src, dest in rename_keys:
        rename_key(state_dict, src, dest)

    # some keys can be renamed efficiently
    for key, val in state_dict.copy().items():
        val = state_dict.pop(key)
        if key.startswith("Qformer.bert"):
            key = key.replace("Qformer.bert", "qformer")
        if "attention.self" in key:
            key = key.replace("self", "attention")
        if "opt_proj" in key:
            key = key.replace("opt_proj", "language_projection")
        if "t5_proj" in key:
            key = key.replace("t5_proj", "language_projection")
        if key.startswith("opt"):
            key = key.replace("opt", "language")
        if key.startswith("t5"):
            key = key.replace("t5", "language")
        state_dict[key] = val

    # read in qv biases
    read_in_q_v_bias(state_dict, config)

    missing_keys, unexpected_keys = hf_model.load_state_dict(state_dict, strict=False)
    assert len(missing_keys) == 0

    if "itm" in model_name:
        unexpected_keys = list(filter(lambda x: not x.startswith("Qformer.cls"), unexpected_keys))
        assert unexpected_keys == ["temp", "qformer.embeddings.position_ids"]
    else:
        assert unexpected_keys == ["qformer.embeddings.position_ids"]

    image = load_demo_image()
    original_pixel_values = vis_processors["eval"](image).unsqueeze(0).to(lavis_device)

    # create processor
    image_processor = BlipImageProcessor(
        size={"height": image_size, "width": image_size}, image_mean=OPENAI_CLIP_MEAN, image_std=OPENAI_CLIP_STD
    )
    processor = Blip2Processor(image_processor=image_processor, tokenizer=tokenizer)
    pixel_values = processor(images=image, return_tensors="pt").pixel_values.to(hf_model_device)

    # make sure processor creates exact same pixel values
    assert torch.allclose(pixel_values, original_pixel_values.to(pixel_values.device))

    original_model.to(lavis_device)
    hf_model.to(hf_model_device)

    if "itm" in model_name:
        caption = "a large fountain spewing water into the air"
        input_ids = tokenizer([caption], return_tensors="pt").input_ids.to(hf_model_device)
        attention_mask = processor(text=caption, return_tensors="pt").attention_mask.to(hf_model_device)

        with torch.no_grad():
            original_logits = original_model(
                {"image": original_pixel_values, "text_input": [caption]}, match_head="itm"
            )
            logits = hf_model(
                pixel_values=pixel_values,
                input_ids=input_ids,
                attention_mask=attention_mask,
                use_image_text_matching_head=True,
            )

        assert original_logits.shape == logits.logits_per_image.shape
        print("First values of original logits:", original_logits[0, :3])
        print("First values of HF logits:", logits.logits_per_image[0, :3])

        # assert values
        # cast to same type
        target_dtype = logits.logits_per_image.dtype
        assert torch.allclose(original_logits.to(target_dtype), logits.logits_per_image, atol=1e-4)

        original_itm_scores = torch.nn.functional.softmax(original_logits, dim=1)
        itm_scores = torch.nn.functional.softmax(logits.logits_per_image, dim=1)
        assert torch.allclose(original_itm_scores.to(target_dtype), itm_scores, atol=1e-4)
        print("Looks ok!")

        with torch.no_grad():
            original_logits = original_model(
                {"image": original_pixel_values, "text_input": [caption]}, match_head="itc"
            )
            logits = hf_model(
                pixel_values=pixel_values,
                input_ids=input_ids,
                attention_mask=attention_mask,
                use_image_text_matching_head=False,
            )

        assert original_logits.shape == logits.logits_per_image.shape
        print("First values of original logits:", original_logits[0, :3])
        print("First values of HF logits:", logits.logits_per_image[0, :3])

        # assert values
        # cast to same type
        target_dtype = logits.logits_per_image.dtype
        assert torch.allclose(original_logits.to(target_dtype), logits.logits_per_image, atol=1e-4)
        print("Looks ok!")

    else:
        input_ids = tokenizer(["\n"], return_tensors="pt").input_ids.to(hf_model_device)

        with torch.no_grad():
            if "opt" in model_name:
                original_logits = original_model({"image": original_pixel_values, "text_input": [""]}).logits
                logits = hf_model(pixel_values, input_ids).logits
            else:
                original_logits = original_model(
                    {"image": original_pixel_values, "text_input": ["\n"], "text_output": ["\n"]}
                ).logits
                labels = input_ids.masked_fill(input_ids == tokenizer.pad_token_id, -100)
                logits = hf_model(pixel_values, input_ids, labels=labels).logits

        assert original_logits.shape == logits.shape
        print("First values of original logits:", original_logits[0, :3, :3])
        print("First values of HF logits:", logits[0, :3, :3])

        # assert values
        assert torch.allclose(original_logits.to(logits.device), logits, atol=1e-4)
        print("Looks ok!")

        print("Generating a caption...")
        prompt = "Question: what object is in this image? Answer:"
        input_ids = tokenizer(prompt, return_tensors="pt").input_ids.to(hf_model_device)

        set_seed(42)

        original_outputs = original_model.generate(
            {"image": original_pixel_values, "prompt": prompt}, use_nucleus_sampling=True, max_length=50
        )
        outputs = hf_model.generate(
            pixel_values,
            input_ids,
            do_sample=True,
            num_beams=5,
            max_length=30,
            min_length=1,
            top_p=0.9,
            repetition_penalty=1.0,
            length_penalty=1.0,
            temperature=1,
        )
        output_text = processor.batch_decode(outputs, skip_special_tokens=True)
        output_text = [text.strip() for text in output_text]
        print("Original generation:", original_outputs)
        print("HF generation:", output_text)

    if pytorch_dump_folder_path is not None:
        processor.save_pretrained(pytorch_dump_folder_path)
        hf_model.save_pretrained(pytorch_dump_folder_path)

    if push_to_hub:
        processor.push_to_hub(f"nielsr/{model_name}")
        hf_model.push_to_hub(f"nielsr/{model_name}")