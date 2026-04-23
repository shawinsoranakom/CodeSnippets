def init_fn(script_module) -> None:
        # Initialize the ScriptModule:
        # 1. Copy the attributes/parameters/buffers from the original `nn_module` to the new ScriptModule.
        for name in concrete_type.get_attributes():
            orig_value = getattr(nn_module, name)
            orig_value = (
                orig_value.value
                if isinstance(orig_value, torch.jit.Attribute)
                else orig_value
            )
            cpp_module.setattr(name, orig_value)

        # 2. Copy the submodules from the original `nn_module` to the new ScriptModule,
        #    recursively scripting them.
        for name, sub_concrete_type in concrete_type.get_modules():
            orig_value = getattr(nn_module, name)
            if not isinstance(orig_value, Module):
                raise AssertionError(f"Expected Module but got {type(orig_value)}")
            module_type = sub_concrete_type.jit_type
            if isinstance(module_type, torch._C.InterfaceType):
                # use the interface inference rule to compile the module
                scripted = interface_script(module_type, orig_value)
            elif isinstance(orig_value, torch.jit.ScriptModule):
                scripted = orig_value
            else:
                # always reuse the provided stubs_fn to infer the methods to compile
                scripted = create_script_module_impl(
                    orig_value, sub_concrete_type, stubs_fn
                )

            cpp_module.setattr(name, scripted)
            script_module._modules[name] = scripted

        # 3. Copy @ignored/@unused methods and attrs from the original `nn_module` to the new ScriptModule.
        #    This ensures we can access these Python methods on the ScriptModule.
        for name in dir(nn_module):
            if name in ignored_properties:
                continue
            item = getattr(nn_module, name, None)
            if inspect.ismethod(item) and _jit_internal.is_ignored_fn(item):
                unbound_function = getattr(nn_module, name).__func__
                bound_method = unbound_function.__get__(script_module)
                setattr(script_module, name, bound_method)
            elif concrete_type.is_ignored_attribute(name):
                setattr(script_module, name, item)

        # For convenience, attach the concrete type to the new ScriptModule
        script_module._concrete_type = concrete_type