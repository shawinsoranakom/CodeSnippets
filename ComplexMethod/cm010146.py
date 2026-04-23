def _fakify_script_objects(
    mod: torch.nn.Module,
    args: Sequence[Any],
    kwargs: dict[Any, Any],
    fake_mode: torch._subclasses.fake_tensor.FakeTensorMode | None,
):
    # This context manager is used to fakify script objects into FakeScriptObject.
    # Inputs:
    #   mod: the module to be exported, it (and its recursive submodules)'s script object attrs haven't been fakified.
    #   args, kwargs: the args and kwargs inputs for mod, script object inputs haven't been fakified.
    #   fake_mode: the fake mode to be used for fakifying script objects. It's the same mode that fakify input tensors.
    #
    # Returns:
    #   mod: the patched module, its (and its recursive submodules) script object attrs have been fakified.
    #   fake_args, fake_kwargs: new fakified args and kwargs.
    #        Script object inputs have been fakified. Don't touch the tensors.
    #   fake_constant_attrs: a new map from FakeScriptObject to the fqn of the original script object.
    #   fake_to_real: a mapping between FakeScriptObject and the original script object in order to un-do the patching.

    constant_attrs: ConstantAttrMap = _gather_constant_attrs(mod)
    if any(isinstance(obj, FakeScriptObject) for obj in constant_attrs.values()):
        raise AssertionError("Mod shouldn't contain any FakeScriptObject.")
    if pytree.tree_any(lambda obj: isinstance(obj, FakeScriptObject), (args, kwargs)):
        raise AssertionError("args and kwargs shouldn't contain any FakeScriptObject.")

    patched_attr = {}
    fake_constant_attrs = ConstantAttrMap()
    fake_to_real = {}

    def _maybe_fakify_obj(obj):
        fake_obj = torch._library.fake_class_registry.maybe_to_fake_obj(fake_mode, obj)
        fake_to_real[fake_obj] = obj
        return fake_obj

    def _leaf_mod_and_attr(
        mod: torch.nn.Module, attr_fqn: str
    ) -> tuple[torch.nn.Module, str]:
        *prefix_attr, last_attr = attr_fqn.split(".")
        cur_mod = mod
        for attr in prefix_attr:
            cur_mod = getattr(cur_mod, attr)
        return cur_mod, last_attr

    try:
        for obj, fqns in constant_attrs.items():
            if torch._library.fake_class_registry._is_script_object(
                obj
            ) or is_opaque_value(obj):
                fake_script_obj = _maybe_fakify_obj(obj)
                for fqn in fqns:
                    cur_mod, attr = _leaf_mod_and_attr(mod, fqn)
                    if obj is not getattr(cur_mod, attr):
                        raise AssertionError(
                            f"obj mismatch at {fqn}: expected {obj}, got {getattr(cur_mod, attr)}"
                        )
                    setattr(cur_mod, attr, fake_script_obj)
                    fake_constant_attrs.add(fake_script_obj, fqn)
                    patched_attr[fqn] = obj
            else:
                for fqn in fqns:
                    fake_constant_attrs.add(obj, fqn)

        fake_args, fake_kwargs = pytree.tree_map_only(
            torch.ScriptObject, _maybe_fakify_obj, (args, kwargs)
        )
        yield (mod, fake_args, fake_kwargs, fake_constant_attrs, fake_to_real)
    finally:
        for fqn, orig_obj in patched_attr.items():
            cur_mod, attr = _leaf_mod_and_attr(mod, fqn)
            setattr(cur_mod, attr, orig_obj)