def get_blip2_config(model_name, eos_token_id):
    image_size = 364 if "coco" in model_name else 224
    vision_config = Blip2VisionConfig(image_size=image_size).to_dict()

    # make sure the models have proper bos_token_id and eos_token_id set (important for generation)
    # seems like flan-T5 models don't have bos_token_id properly set?
    if "opt-2.7b" in model_name:
        text_config = OPTConfig.from_pretrained("facebook/opt-2.7b", eos_token_id=eos_token_id).to_dict()
    elif "opt-6.7b" in model_name:
        text_config = OPTConfig.from_pretrained("facebook/opt-6.7b", eos_token_id=eos_token_id).to_dict()
    elif "t5-xl" in model_name:
        text_config = T5Config.from_pretrained("google/flan-t5-xl", dense_act_fn="gelu", bos_token_id=1).to_dict()
    elif "t5-xxl" in model_name:
        text_config = T5Config.from_pretrained("google/flan-t5-xxl", dense_act_fn="gelu", bos_token_id=1).to_dict()
    elif "itm" in model_name:
        text_config = {}
    else:
        raise ValueError("Model name not supported")

    if "itm" in model_name:
        config = Blip2Config(
            vision_config=vision_config,
            qformer_config=Blip2QFormerConfig(vocab_size=30523, use_qformer_text_input=True).to_dict(),
        )
    else:
        config = Blip2Config(vision_config=vision_config, text_config=text_config)

    return config, image_size