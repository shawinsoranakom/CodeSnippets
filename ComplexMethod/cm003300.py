def get_git_config(model_name):
    if "base" in model_name and "vqa" in model_name:
        image_size = 480
    elif "large" in model_name and "vqa" in model_name:
        image_size = 420
    else:
        image_size = 224

    vision_config = GitVisionConfig(image_size=image_size)

    if "large" in model_name:
        vision_config.patch_size = 14
        vision_config.hidden_size = 1024
        vision_config.intermediate_size = 4096
        vision_config.num_hidden_layers = 24
        vision_config.num_attention_heads = 16

    is_video = "vatex" in model_name or "msrvtt" in model_name
    num_image_with_embedding = 6 if is_video else None
    config = GitConfig(vision_config=vision_config.to_dict(), num_image_with_embedding=num_image_with_embedding)

    return config, image_size, is_video