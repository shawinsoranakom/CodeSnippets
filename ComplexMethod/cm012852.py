def load_observer_state_dict(mod, obs_dict):
    r"""
    Given input model and a state_dict containing model observer stats,
    load the stats back into the model. The observer state_dict can be saved
    using torch.ao.quantization.get_observer_state_dict
    """
    missing_keys: list[str] = []
    unexpected_keys: list[str] = []
    for name, module in mod.named_modules():
        prefix = name + "."
        if _is_activation_post_process(module):
            if _is_per_channel_script_obs_instance(module):
                # For per-channel observers we need to call a custom load_from_state_dict to resize the tensor.
                # However this is not called when the module is scripted and we end up calling the default one in module.py
                module._load_from_state_dict_script(
                    obs_dict, prefix, {}, True, missing_keys, unexpected_keys, []
                )
            else:
                module._load_from_state_dict(
                    obs_dict, prefix, {}, False, missing_keys, unexpected_keys, []
                )
    for k in missing_keys:
        if "observer" in k or "activation_post_process" in k:
            raise Exception(  # noqa: TRY002
                f"Missing keys for observer {k} in state_dict"
            )
    for k in unexpected_keys:
        if "observer" in k or "activation_post_process" in k:
            raise Exception(  # noqa: TRY002
                f"Unexpected keys for observer {k} in state_dict"
            )