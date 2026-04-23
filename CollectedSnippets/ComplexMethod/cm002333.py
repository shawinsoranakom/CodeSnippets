def replace_class_node(
    mapper: ModelFileMapper, modular_class_node: cst.ClassDef, renamed_super_class: str, original_super_class: str
) -> cst.ClassDef:
    """
    Replace a class node which inherits from another modeling class. This function works in the following way:
    - start from the methods and class attributes of the original modeling code node, and replace their definition
    if overridden in the modular
    - append all new methods and class attributes defined in the child class
    - all potential method/class docstrings and decorators use the ones found in modular if any, else in original modeling
    - replace all calls to super() with the unravelled code

    Args:
        mapper (`ModelFileMapper`):
            The mapper corresponding to the visited file from which the modular class node inherits.
        modular_class_node (`cst.ClassDef`):
            The class node as found in the modular file.
        renamed_super_class (`str`):
            The name of the class from which `modular_class_node` inherits after automatic renaming.
        original_super_class (`str`):
            The name of the class from which `modular_class_node` inherits before automatic renaming.

    Returns:
        A new class node corresponding to the modular definition.
    """
    all_new_bases = {get_full_attribute_name(k.value): k for k in modular_class_node.bases}
    if any(base is None for base in all_new_bases.keys()):
        raise ValueError(f"Could not parse the name of the bases for {modular_class_node.name.value}")

    original_modeling_node = mapper.classes[renamed_super_class]
    # Always use the new name of the class (in case we use e.g. `ColPaliForRetrieval` inheriting from `PaliGemmaForConditionalGeneration`)
    new_class_name = modular_class_node.name

    # If the new class name is different from the renamed super class name, we need to update the docstrings/comments accordingly
    if new_class_name.value != renamed_super_class:
        common_suffix = common_partial_suffix(new_class_name.value, renamed_super_class)
        # Note that this works even without common prefix, in which case it does not replace anything
        old, new = renamed_super_class.replace(common_suffix, ""), new_class_name.value.replace(common_suffix, "")
        temp_module = cst.Module(body=[original_modeling_node])
        original_modeling_node = temp_module.visit(
            ReplaceNameTransformer(get_lowercase_name(old), get_lowercase_name(new), only_doc=True)
        ).body[0]

    # If we explicitly passed a new base with common suffix to an old base, it is for switching the prefix
    # e.g. if the "natural" parent class is `PreTrainedModel` but we wanted to rename it to `PreTrainedVisionModel`
    additional_bases = {base for base in all_new_bases.keys() if base != original_super_class}
    new_class_bases = []
    for original_base in original_modeling_node.bases:
        new_base = original_base
        # we only potentially switch base for Name-based bases, not Attribute
        if m.matches(original_base.value, m.Name()):
            original_base_name = original_base.value.value
            for additional_base_name in additional_bases:
                suffix = common_partial_suffix(original_base_name, additional_base_name)
                if len(suffix) > 0 and suffix[0].isupper():
                    new_name_node = original_base.value.with_changes(value=additional_base_name)
                    new_base = original_base.with_changes(value=new_name_node)
                    # Remove from set
                    additional_bases.discard(additional_base_name)
                    break
        new_class_bases.append(new_base)
    # Add potential additional classes that may not be inherited as the parent does not use them, and that were not
    # already replaced above
    original_bases = {get_full_attribute_name(k.value) for k in original_modeling_node.bases}
    new_class_bases.extend(
        [all_new_bases[added_base] for added_base in additional_bases if added_base not in original_bases]
    )
    # If we have both `nn.Module` and `GradientCheckpointingLayer`, remove `nn.Module`
    new_class_bases_names = {get_full_attribute_name(k.value) for k in new_class_bases}
    if "nn.Module" in new_class_bases_names and "GradientCheckpointingLayer" in new_class_bases_names:
        new_class_bases = [k for k in new_class_bases if get_full_attribute_name(k.value) != "nn.Module"]

    # Use class decorators redefined in modular file if any
    new_class_decorators = (
        modular_class_node.decorators if len(modular_class_node.decorators) > 0 else original_modeling_node.decorators
    )

    # Compute new class docstring
    original_modeling_docstring = [
        node for node in original_modeling_node.body.body if m.matches(node, DOCSTRING_NODE)
    ]
    modular_docstring = [node for node in modular_class_node.body.body if m.matches(node, DOCSTRING_NODE)]
    # Use class docstring in modular if any, else original modeling code docstring
    new_class_docstring = modular_docstring if len(modular_docstring) > 0 else original_modeling_docstring

    # Compute new class attributes
    original_modeling_class_attributes = {}
    for node in original_modeling_node.body.body:
        if m.matches(node, m.SimpleStatementLine(body=[m.Assign()])):
            original_modeling_class_attributes[node.body[0].targets[0].target.value] = node
        elif m.matches(node, m.SimpleStatementLine(body=[m.AnnAssign()])):
            original_modeling_class_attributes[node.body[0].target.value] = node

    modular_class_attributes = {}
    for node in modular_class_node.body.body:
        if m.matches(node, m.SimpleStatementLine(body=[m.Assign()])):
            if hasattr(node.body[0].value, "func") and node.body[0].value.func.value == "AttributeError":
                original_modeling_class_attributes.pop(node.body[0].targets[0].target.value)
                continue  # delete unnecessary cls attribute, especially in configs
            modular_class_attributes[node.body[0].targets[0].target.value] = node
        elif m.matches(node, m.SimpleStatementLine(body=[m.AnnAssign()])):
            modular_class_attributes[node.body[0].target.value] = node

    # Use all original modeling attributes, and potentially override some with values in the modular
    new_class_attributes = list({**original_modeling_class_attributes, **modular_class_attributes}.values())

    # Check class methods defined in the modular and associated modeling
    original_modeling_methods = {}
    for node in original_modeling_node.body.body:
        if m.matches(node, m.FunctionDef()):
            # Due to the @property and @name.setter decorators, methods can sometimes have the same name, so we need a way
            # to separate them
            if node.name.value in original_modeling_methods:
                # If it's already present, and the decorator is @property, it means the node already added was the setter
                if node.decorators[0].decorator.value == "property":
                    original_modeling_methods[f"{node.name.value}_setter"] = original_modeling_methods[node.name.value]
                    original_modeling_methods[node.name.value] = node
                # In this case current node is the setter
                else:
                    original_modeling_methods[f"{node.name.value}_setter"] = node
            else:
                original_modeling_methods[node.name.value] = node
    modular_methods = {}
    for node in modular_class_node.body.body:
        if m.matches(node, m.FunctionDef()):
            # Due to the @property and @name.setter decorators, methods can sometimes have the same name, so we need a way
            # to separate them
            if node.name.value in modular_methods:
                # If it's already present, and the decorator is @property, it means the node already added was the setter
                if node.decorators[0].decorator.value == "property":
                    modular_methods[f"{node.name.value}_setter"] = modular_methods[node.name.value]
                    modular_methods[node.name.value] = node
                # In this case current node is the setter
                else:
                    modular_methods[f"{node.name.value}_setter"] = node
            else:
                modular_methods[node.name.value] = node

    new_class_methods = []
    # Iterate over the methods of the original modeling code, and add them to the list of methods to add
    for name, node in original_modeling_methods.items():
        # If the method was redefined in modular, make appropriate changes to the node
        if name in modular_methods:
            # Get the corresponding method node in modular
            modular_node = modular_methods[name]

            # If we match the pattern, we should avoid inheriting the method
            if re.match(
                r"\ndef .*\(.*\).*:.*\n    raise.*Error\(.*", mapper.python_module.code_for_node(modular_node)
            ):
                continue

            # Compute new method docstring
            modeling_docstring = [node_ for node_ in node.body.body if m.matches(node_, DOCSTRING_NODE)]
            modular_docstring = [node_ for node_ in modular_node.body.body if m.matches(node_, DOCSTRING_NODE)]
            # Use method docstring in modular if any, else original modeling code docstring
            new_body = (
                modular_node.body.body
                if len(modular_docstring) > 0
                else modeling_docstring + list(modular_node.body.body)
            )
            new_body = modular_node.body.with_changes(body=new_body)

            # Use arguments as defined in the modular
            new_params = modular_node.params

            # If using the `**super_kwargs` syntax in modular, merge any existing modular arg with all the original modeling ones
            kwarg_name = getattr(modular_node.params, "star_kwarg", None)
            if kwarg_name and kwarg_name.name.value == "super_kwargs":
                original_modeling_params = {k.name.value: k for k in node.params.params}
                modular_params = {k.name.value: k for k in new_params.params[1:]}
                new_param_list = list({**original_modeling_params, **modular_params}.values())
                new_params = new_params.with_changes(params=new_param_list, star_kwarg=node.params.star_kwarg)

            # Keep decorators in modular if any, else original decorators
            new_decorators = modular_node.decorators if len(modular_node.decorators) > 0 else node.decorators

            # Keep return annotation in modular if any, else original return annotation
            new_return_annotation = modular_node.returns if modular_node.returns else node.returns

            # Update the method node
            node = node.with_changes(
                body=new_body,
                params=new_params,
                decorators=new_decorators,
                returns=new_return_annotation,
            )

        new_class_methods.append(node)

    # Port new methods that are defined only in modular-file and append at the end
    for name, node in modular_methods.items():
        if name not in original_modeling_methods:
            new_class_methods.append(node)

    # Recreate the whole new class body
    new_class_body = new_class_docstring + new_class_attributes + new_class_methods

    # if renamed_super_class == "Aimv2Config":
    # Replace the calls to `super()` of the redefined modular methods with the unrolled code
    result_node = original_modeling_node.with_changes(body=cst.IndentedBlock(body=new_class_body))
    temp_module = cst.Module(body=[result_node])
    new_replacement_class = temp_module.visit(
        ReplaceSuperCallTransformer(temp_module, original_modeling_methods, modular_methods, new_class_bases)
    )
    new_class_body = new_replacement_class.body[0].body  # get the indented block

    return original_modeling_node.with_changes(
        body=new_class_body, decorators=new_class_decorators, bases=new_class_bases, name=new_class_name
    )