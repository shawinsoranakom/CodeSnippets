def get_attributes(cls):
        args_in_init = inspect.signature(cls.__init__).parameters.keys()
        attributes = []
        for sub_processor_type in args_in_init:
            # don't treat audio_tokenizer as an attribute
            if sub_processor_type == "audio_tokenizer":
                continue
            if any(modality in sub_processor_type for modality in MODALITY_TO_AUTOPROCESSOR_MAPPING.keys()):
                attributes.append(sub_processor_type)

        # Legacy processors may not override `__init__` and instead expose modality
        # attributes via `<attribute>_class`. In that case, `args_in_init` only exposes
        # `*args`/`**kwargs`, so we need to infer the attributes from those class-level
        # hints to keep backward compatibility (e.g. dynamic processors stored on the Hub).
        if not attributes:
            for attribute_name, value in cls.__dict__.items():
                if value is None or attribute_name == "audio_tokenizer_class" or not attribute_name.endswith("_class"):
                    continue
                inferred_attribute = attribute_name[: -len("_class")]
                if inferred_attribute == "audio_tokenizer":
                    continue
                if any(modality in inferred_attribute for modality in MODALITY_TO_AUTOPROCESSOR_MAPPING.keys()):
                    attributes.append(inferred_attribute)

        return attributes