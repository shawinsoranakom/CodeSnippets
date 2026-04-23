def _get_fqns(
    model: nn.Module,
    name: str,
    dsd_fqn_modifiers: str = "_fqn_modifiers",
    skip_ddp_prefix: bool = True,
    skip_compiler_prefix: bool = True,
) -> FQNS_T:
    """
    This API is used to convert the name of a parameter to the FQNs. For FSDP
    without `use_orig_params`, the name of FlatParameter can be mapped to
    multiple original parameters. As a result, the return type of this function
    is `set[str]`.

    Args:
        module (nn.Module): the root model.
        name (str): the name
        skip_ddp_prefix (bool): whether to skip DDP's `module` prefix

    Returns:
        The canonical FQNs based on the model traversal.
    """

    # Remove the checkpoint prefix, if it exists.
    name = name.replace(_CHECKPOINT_PREFIX, "")
    if "." not in name:
        return {name}

    obj_names = name.split(".")
    fqn_obj_names = []
    curr_obj = model
    for i, curr_obj_name in enumerate(obj_names):
        if isinstance(curr_obj, DDP):
            if curr_obj_name != "module":
                raise AssertionError(f"Expected 'module', got '{curr_obj_name}'")
            curr_obj = curr_obj.module
            if not skip_ddp_prefix:
                fqn_obj_names.append(curr_obj_name)
        elif isinstance(curr_obj, FSDP):
            if i < len(obj_names) - 1 and obj_names[i + 1] == _FLAT_PARAM:
                prefix = ".".join(fqn_obj_names)
                flat_param = getattr(curr_obj, _FLAT_PARAM)
                if prefix:
                    prefix = f"{prefix}."
                return {f"{prefix}{fqn}" for fqn in flat_param._fqns}
            curr_obj = getattr(curr_obj, FSDP_WRAPPED_MODULE)
            if curr_obj_name != FSDP_WRAPPED_MODULE:
                fqn_obj_names.append(curr_obj_name)
                curr_obj = getattr(curr_obj, curr_obj_name)
        elif isinstance(curr_obj, torch._dynamo.eval_frame.OptimizedModule):
            if curr_obj_name != "_orig_mod":
                raise AssertionError(f"Expected '_orig_mod', got '{curr_obj_name}'")
            curr_obj = curr_obj._orig_mod
            if not skip_compiler_prefix:
                fqn_obj_names.append(curr_obj_name)
        else:
            # In some modules, _fqn_modifiers would not shown in the state_dict keys,
            # skip them in the fqn to ensure load stat dict successfully for them.
            if hasattr(curr_obj, dsd_fqn_modifiers):
                if removed_fqn := getattr(curr_obj, dsd_fqn_modifiers)().get(
                    curr_obj_name
                ):
                    if hasattr(curr_obj, removed_fqn):
                        curr_obj = getattr(curr_obj, removed_fqn)
            fqn_obj_names.append(curr_obj_name)
            if curr_obj_name == nn.modules.module._EXTRA_STATE_KEY_SUFFIX:
                if i != len(obj_names) - 1:
                    raise RuntimeError("Expect `_extra_state` to be the last obj name")
            else:
                curr_obj = getattr(curr_obj, curr_obj_name)

    return {".".join(fqn_obj_names).replace(_CHECKPOINT_PREFIX, "")}