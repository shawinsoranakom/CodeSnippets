def _get_exact_config(_config, config_class):
    # TODO: we probably needs to make sure they are equal class, not just instance
    if _config.__class__ == config_class:
        return _config

    # TODO: T5Gemma2 has `encoder` and `decoder` instead `_config`

    # We consider both cases: real config or dict (for `FastSpeech2ConformerConfig`'s encoder/decoder config, which are only module config)
    config_dict = _config.to_dict() if not isinstance(_config, dict) else _config

    keys = [x for x in config_dict.keys() if x.endswith("_config") or x in ["encoder", "decoder"]]

    # TODO: For `VibeVoiceAcousticTokenizer`, it doesn't have `encoder_config` or `decoder_config` when converted to dict
    # but it has this properties.
    if not isinstance(_config, dict):
        for attr in dir(_config):
            if attr.endswith("_config") or attr in ["encoder", "decoder"]:
                # TODO: damm, we have some `get_text_config` (and maybe others) which is function!!!
                # For property, it's not callable!
                if callable(getattr(_config, attr, None)):
                    continue

                keys.append(attr)

    for key in keys:
        sub_config = getattr(_config, key) if not isinstance(_config, dict) else _config[key]
        if sub_config is not None:
            # TODO: `VibeVoiceAcousticTokenizerEncoder/DecoderConfig` needs some protection!!!
            if sub_config.__class__ == _config.__class__:
                continue
            maybe_config = _get_exact_config(sub_config, config_class)
            if isinstance(maybe_config, config_class):
                return maybe_config

    return _config