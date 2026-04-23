def infer_concrete_type_builder(nn_module, share_types=True):
    """
    Build a ConcreteModuleTypeBuilder from an nn.Module.

    This ConcreteModuleType doesn't have a JIT type associated with it yet, it
    must be filled in by the caller.
    """
    concrete_type_builder = torch._C.ConcreteModuleTypeBuilder(type(nn_module))
    if isinstance(nn_module, (torch.nn.ModuleDict)):
        concrete_type_builder.set_module_dict()
    if isinstance(nn_module, (torch.nn.ModuleList, torch.nn.Sequential)):
        concrete_type_builder.set_module_list()
    if isinstance(nn_module, (torch.nn.ParameterList)):
        concrete_type_builder.set_parameter_list()
    if isinstance(nn_module, (torch.nn.ParameterDict)):
        concrete_type_builder.set_parameter_dict()

    class_annotations = get_annotations(nn_module)
    if isinstance(nn_module, (torch.ao.quantization.QuantWrapper)):
        class_annotations = {}

    # Get user-annotated ignored attributes.
    user_annotated_ignored_attributes = getattr(
        nn_module, "__jit_ignored_attributes__", []
    )
    concrete_type_builder.add_ignored_attributes(user_annotated_ignored_attributes)
    ignored_properties = jit_ignored_properties(nn_module)

    # try to infer the type from type annotation or from the object itself
    def infer_type(name, item):
        # The forward function from Module is special; never use this annotations; we
        # need to infer type directly using JIT.  I originally wanted to write
        # this test as isinstance(class_annotations[name], Callable) but
        # isinstance on typing things doesn't seem to work: isinstance(list, Callable)
        # is also true!
        inferred = False
        try:
            if (
                name in class_annotations
                and class_annotations[name]
                != torch.nn.Module.__annotations__["forward"]
            ):
                ann_to_type = torch.jit.annotations.ann_to_type(
                    class_annotations[name], fake_range()
                )
                attr_type = torch._C.InferredType(ann_to_type)
            elif isinstance(item, torch.jit.Attribute):
                ann_to_type = torch.jit.annotations.ann_to_type(item.type, fake_range())
                attr_type = torch._C.InferredType(ann_to_type)
            else:
                attr_type = torch._C._jit_try_infer_type(item)
                inferred = True
        except RuntimeError as re:
            raise RuntimeError(f"Error inferring type for {name}: {item}: {re}") from re

        return attr_type, inferred

    added_names = set()

    for name, item in nn_module._parameters.items():
        if name in user_annotated_ignored_attributes:
            continue

        if not (item is None or isinstance(item, torch.Tensor)):
            raise AssertionError(
                f"Expected parameter '{name}' to be None or Tensor, got {type(item)}"
            )
        attr_type, _ = infer_type(name, item)
        # We currently have the invariant in various places in our code
        # that parameters must be Tensors. However, the nn.Module API also
        # allows NoneType parameters. These parameters are not returned as
        # part of `parameters()` and its variants, but are available
        # through direct attribute access.
        concrete_type_builder.add_attribute(name, attr_type.type(), True, False)
        added_names.add(name)

    for name, item in nn_module._buffers.items():
        if name in user_annotated_ignored_attributes:
            continue

        if not (item is None or isinstance(item, torch.Tensor)):
            raise AssertionError(
                f"Expected buffer '{name}' to be None or Tensor, got {type(item)}"
            )
        attr_type, _ = infer_type(name, item)
        concrete_type_builder.add_attribute(name, attr_type.type(), False, True)
        added_names.add(name)

    for name, item in nn_module._modules.items():
        if name in user_annotated_ignored_attributes:
            continue

        attr_type, _ = infer_type(name, item)
        if item is None:
            # Modules can be None. We don't have direct support for optional
            # Modules, so the register it as an NoneType attribute instead.
            concrete_type_builder.add_attribute(name, attr_type.type(), False, False)
            continue
        if attr_type.success():
            if not attr_type.type().is_interface_type():
                raise AssertionError(
                    f"Expected inferred type to be interface type for '{name}'"
                )
            # if the type can be inferred, it should be a module interface type
            sub_concrete_type = torch._C.ConcreteModuleType.from_jit_type(
                attr_type.type()
            )
        else:
            # otherwise we get the concrete module type for item and add it to concrete_type
            sub_concrete_type = get_module_concrete_type(item, share_types)
        concrete_type_builder.add_module(name, sub_concrete_type)

        added_names.add(name)

    # populate constants_set
    constants_set = set(getattr(nn_module, "__constants__", ()))

    # Constants annotated via `Final[T]` rather than being added to `__constants__`
    for name, ann in class_annotations.items():
        if torch._jit_internal.is_final(ann):
            constants_set.add(name)

    for name in constants_set:
        if name in added_names:
            # TODO: We should really error in this case, but its bc-breaking so
            # we need to warn for at least one release
            if name in nn_module._modules:
                hint = "submodule"
            elif name in nn_module._buffers:
                hint = "buffer"
            elif name in nn_module._parameters:
                hint = "parameter"
            else:
                raise AssertionError(
                    "added_names must be submodule, parameter, or buffer"
                )

            warnings.warn(
                f"'{name}' was found in ScriptModule constants, "
                f" but it is a non-constant {hint}. Consider removing it.",
                stacklevel=2,
            )
            continue
        if not hasattr(nn_module, name):
            # TODO: We should really error in this case, but its bc-breaking so
            # we need to warn for at least one release
            warnings.warn(
                f"'{name}' was found in ScriptModule constants, "
                "but was not actually set in __init__. "
                "Consider removing it.",
                stacklevel=2,
            )
            continue
        value = getattr(nn_module, name)
        concrete_type_builder.add_constant(
            name, _get_valid_constant(name, value, type(nn_module).__name__)
        )
        added_names.add(name)

    # populate overloads
    overloads = getattr(nn_module, "__overloads__", {})
    # update with any annotated overloads
    overloads.update(
        get_overload_name_mapping(
            get_overload_annotations(nn_module, ignored_properties)
        )
    )
    for name, overloaded_names in overloads.items():
        concrete_type_builder.add_overload(name, overloaded_names)

    for name, value in nn_module.__dict__.items():
        if name in ignored_attributes or name.startswith("__"):
            # Python objects have lots of random attributes attached to them;
            # PyTorch adds a few more. Prevent these from getting compiled.
            continue

        if name in user_annotated_ignored_attributes:
            continue

        if name in added_names:
            # Don't re-add anything we already added
            continue

        isoverloadpacket = isinstance(value, torch._ops.OpOverloadPacket)
        if isoverloadpacket:
            value = value.op
        # Handle Python function attributes
        if inspect.isfunction(value):
            try:
                scripted_fn = torch.jit.script(value)
                concrete_type_builder.add_function_attribute(
                    name, torch._C._jit_try_infer_type(scripted_fn).type(), value
                )
            except Exception as e:
                # If we fail to script the function, it isn't a hard error.
                # Instead, we will add it to the list of attributes we failed
                # to convert, with the compilation error.
                hint = (
                    "(This function exists as an attribute on the Python module, "
                    "but we failed to compile it to a TorchScript function. "
                    f"\nThe error stack is reproduced here:\n{e})"
                )
                concrete_type_builder.add_failed_attribute(name, hint)

            continue

        # Handle calls to builtin functions (either bespoke builtins from torch.jit._builtins or
        # a call to an aten function like torch.add)
        builtin_symbol_name = _find_builtin(value)
        if builtin_symbol_name:
            concrete_type_builder.add_builtin_function(name, builtin_symbol_name)
            continue

        # Handle Script function attributes
        if isinstance(value, torch.jit.ScriptFunction):
            concrete_type_builder.add_function_attribute(
                name, torch._C._jit_try_infer_type(value).type(), value
            )
            continue

        # If we got here, this is a regular "data" attribute, add it to the concrete type
        attr_type, inferred = infer_type(name, value)
        if attr_type.success():
            concrete_type_builder.add_attribute(name, attr_type.type(), False, False)
        else:
            # TODO: could add more detail here. For example, what the user should do
            # when the pytype is `list` or `NoneType`
            inferred_msg = (
                "Its type was inferred; try adding a type annotation for the attribute."
                if inferred
                else ""
            )
            additional_info = f"{attr_type.reason()}. {inferred_msg}"
            hint = (
                "(This attribute exists on the Python module, "
                f"but we failed to convert Python type: '{torch.typename(type(value))}' "
                f"to a TorchScript type. {additional_info})"
            )
            concrete_type_builder.add_failed_attribute(name, hint)

    # add hooks to concrete type
    for hook in nn_module._forward_hooks.values():
        concrete_type_builder.add_forward_hook(hook)
    for pre_hook in nn_module._forward_pre_hooks.values():
        concrete_type_builder.add_forward_pre_hook(pre_hook)

    return concrete_type_builder