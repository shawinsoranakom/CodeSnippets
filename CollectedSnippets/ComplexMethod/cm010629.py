def create_script_module_impl(nn_module, concrete_type, stubs_fn):
    """
    Convert an nn.Module to a RecursiveScriptModule.

    Args:
        nn_module:  The original Python nn.Module that we are creating a ScriptModule for.
        concrete_type:  The fully initialized ConcreteType of the module.
        stubs_fn:  Lambda that takes an nn.Module and generates a list of ScriptMethodStubs to compile.
    """
    cpp_module = torch._C._create_module_with_type(concrete_type.jit_type)
    method_stubs = stubs_fn(nn_module)
    property_stubs = get_property_stubs(nn_module)
    hook_stubs, pre_hook_stubs = get_hook_stubs(nn_module)
    ignored_properties = jit_ignored_properties(nn_module)

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

    # Actually create the ScriptModule, initializing it with the function we just defined
    script_module = torch.jit.RecursiveScriptModule._construct(cpp_module, init_fn)

    # Compile methods if necessary
    if concrete_type not in concrete_type_store.methods_compiled:
        create_methods_and_properties_from_stubs(
            concrete_type, method_stubs, property_stubs
        )
        # Create hooks after methods to ensure no name collisions between hooks and methods.
        # If done before, hooks can overshadow methods that aren't exported.
        create_hooks_from_stubs(concrete_type, hook_stubs, pre_hook_stubs)
        torch._C._run_emit_module_hook(cpp_module)
        concrete_type_store.methods_compiled.add(concrete_type)

    # Copy the forward hooks and pre-hooks to the new ScriptModule
    # to allow the hooks to be run from eager as ScriptFunctions
    for idx, fn in enumerate(script_module._c._get_forward_pre_hooks()):
        script_module._forward_pre_hooks[idx] = fn
    for idx, fn in enumerate(script_module._c._get_forward_hooks()):
        script_module._forward_hooks[idx] = fn

    # Special handling so methods like __len__ work in script methods on classes derived from containers
    if (
        isinstance(
            nn_module, (torch.nn.ModuleList, torch.nn.Sequential, torch.nn.ModuleDict)
        )
        and "__len__" not in cpp_module._method_names()
    ):
        script_module.define(f"def __len__(self):\n   return {len(nn_module)}\n")
    if (
        isinstance(nn_module, torch.nn.ModuleDict)
        and "__contains__" not in cpp_module._method_names()
    ):
        if len(nn_module.keys()):
            keys = repr(list(nn_module.keys()))
            script_module.define(
                f"def __contains__(self, key: str):\n   return key in {keys}\n"
            )
        else:
            script_module.define("def __contains__(self, key: str):\n   return False\n")

    # Make the compiled methods available to the Python ScriptModule class.
    for method_stub in method_stubs:
        if method_stub.original_method is None:
            # define()'d methods don't have an Python original_method, so we
            # don't need to do any Python re-wrapping stuff
            continue

        name = method_stub.original_method.__name__
        if name != method_stub.def_.name().name:
            # TODO: Why skip this? Because @torch.jit._overload_method will
            # mangle the name of the function.
            continue
        script_method = cpp_module._get_method(name)

        # Wrap the original to propagate docstrings and such.
        # TODO: we don't currently do this functions that are recursively
        # compiled, we should.
        wrapped_script_method = functools.wraps(method_stub.original_method)(
            script_method
        )

        # Add the methods to the script_module directly. This ensures they will
        # be found first when `name` is looked up (as opposed to the stubs or
        # nn.Module.forward)
        script_module.__dict__[name] = wrapped_script_method

    # Make module properties available on the Python ScriptModule class.
    for property_stub in property_stubs:
        property_name = property_stub.def_.name().name
        fget = cpp_module._get_method(property_stub.def_.getter_name().name)
        # Setter is optional, so it may not exist.
        setter_name = property_stub.def_.setter_name()
        fset = cpp_module._get_method(setter_name.name) if setter_name else None
        script_module.__dict__[property_name] = property(property_name, fget, fset)  # type: ignore[arg-type]

    # copy over python methods to script module if they aren't defined on the script module
    # this is currently an internal api used only on module containers
    for name in dir(nn_module):
        if name in ignored_properties:
            continue
        item = getattr(nn_module, name, None)
        if (
            _jit_internal.get_torchscript_modifier(item)
            is _jit_internal.FunctionModifiers.COPY_TO_SCRIPT_WRAPPER
        ):
            add_python_attr_to_scripted_model(script_module, nn_module, name)

    return script_module