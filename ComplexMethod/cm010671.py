def call_prepare_scriptable_func_impl(obj, memo):
    if not isinstance(obj, torch.nn.Module):
        return obj

    obj_id = id(obj)

    # If obj_id is in memo, obj has already been prepared or is being
    # prepared in another call up the stack.
    if obj_id in memo:
        return memo[id(obj)]

    obj = (
        # pyrefly: ignore [not-callable]
        obj.__prepare_scriptable__() if hasattr(obj, "__prepare_scriptable__") else obj
    )  # type: ignore[operator]
    # Record obj in memo to avoid infinite recursion in the case of cycles in the module
    # hierarchy when recursing below.
    memo[obj_id] = obj

    new_obj_dict = {}

    for name, sub_module in obj.__dict__.items():
        if name == "_modules":
            for k, v in sub_module.items():
                sub_module[k] = call_prepare_scriptable_func_impl(v, memo)
            new_obj_dict[name] = sub_module
        elif isinstance(sub_module, torch.nn.Module) and not isinstance(
            sub_module, ScriptModule
        ):
            new_obj_dict[name] = call_prepare_scriptable_func_impl(sub_module, memo)
        else:
            new_obj_dict[name] = sub_module

    for v in new_obj_dict.values():
        obj.__dict__[name] = v

    return obj