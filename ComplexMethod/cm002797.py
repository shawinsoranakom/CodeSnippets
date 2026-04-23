def convert_old_keys_to_new_keys(state_dict_keys: dict | None = None, path: str | None = None):
    """
    This function should be applied only once, on the concatenated keys to efficiently rename using
    the key mappings.
    """
    output_dict = {}
    if state_dict_keys is not None:
        old_text_vision = "\n".join([key for key in state_dict_keys if key.startswith("vision_model")])
        new_text = old_text_vision
        for pattern, replacement in ORIGINAL_TO_CONVERTED_KEY_MAPPING_VISION.items():
            new_text = re.sub(pattern, replacement, new_text)
        output_dict = dict(zip(old_text_vision.split("\n"), new_text.split("\n")))
        old_text_language = "\n".join([key for key in state_dict_keys if key.startswith("language_model")])
        new_text = old_text_language
        if get_lm_type(path) == "llama":
            for pattern, replacement in ORIGINAL_TO_CONVERTED_KEY_MAPPING_TEXT_LLAMA.items():
                new_text = re.sub(pattern, replacement, new_text)
        elif LM_TYPE_CORRESPONDENCE[path] == "qwen2":
            for pattern, replacement in ORIGINAL_TO_CONVERTED_KEY_MAPPING_TEXT_QWEN2.items():
                new_text = re.sub(pattern, replacement, new_text)
        output_dict.update(dict(zip(old_text_language.split("\n"), new_text.split("\n"))))
        old_text_multi = "\n".join(
            [
                key
                for key in state_dict_keys
                if not (key.startswith("language_model") or key.startswith("vision_model"))
            ]
        )
        new_text = old_text_multi
        for pattern, replacement in ORIGINAL_TO_CONVERTED_KEY_MAPPING_MULTI.items():
            new_text = re.sub(pattern, replacement, new_text)
        output_dict.update(dict(zip(old_text_multi.split("\n"), new_text.split("\n"))))

    return output_dict