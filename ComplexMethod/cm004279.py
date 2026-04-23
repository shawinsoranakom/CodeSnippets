def tokenizer_class_from_name(class_name: str) -> type[Any] | None:
    # Bloom tokenizer classes were removed but should map to the fast backend for BC
    if class_name in {"BloomTokenizer", "BloomTokenizerFast"}:
        return TokenizersBackend

    if class_name in REGISTERED_FAST_ALIASES:
        return REGISTERED_FAST_ALIASES[class_name]

    if class_name in REGISTERED_TOKENIZER_CLASSES:
        return REGISTERED_TOKENIZER_CLASSES[class_name]

    if class_name == "TokenizersBackend":
        return TokenizersBackend

    # V5: TOKENIZER_MAPPING_NAMES now maps to single strings, not tuples
    for module_name, tokenizer_class in TOKENIZER_MAPPING_NAMES.items():
        if tokenizer_class == class_name:
            module_name = model_type_to_module_name(module_name)
            if (
                module_name in ["mistral", "mistral3", "mixtral", "ministral", "ministral3", "pixtral", "voxtral"]
                and class_name == "MistralCommonBackend"
            ):
                module = importlib.import_module(".tokenization_mistral_common", "transformers")
            else:
                module = importlib.import_module(f".{module_name}", "transformers.models")
            try:
                result = getattr(module, class_name)
                # BC v5: expose XxxFast alias and tokenization_*_fast submodule for pre-v5 remote code.
                if (submod := getattr(result, "__module__", None)) and submod in sys.modules:
                    base_mod = sys.modules[submod]
                    setattr(base_mod, result.__name__ + "Fast", result)
                    sys.modules.setdefault(submod + "_fast", base_mod)
                return result
            except AttributeError:
                continue

    for tokenizer in TOKENIZER_MAPPING._extra_content.values():
        if getattr(tokenizer, "__name__", None) == class_name:
            return tokenizer

    # We did not find the class, but maybe it's because a dep is missing. In that case, the class will be in the main
    # We did not find the class, but maybe it's because a dep is missing. In that case, the class will be in the main
    # init and we return the proper dummy to get an appropriate error message.
    main_module = importlib.import_module("transformers")
    if hasattr(main_module, class_name):
        return getattr(main_module, class_name)

    # BC v5: If a XxxFast class is not found, retry without 'Fast' for tokenizers saved pre-v5.
    if class_name.endswith("Fast"):
        return tokenizer_class_from_name(class_name[:-4])

    return None