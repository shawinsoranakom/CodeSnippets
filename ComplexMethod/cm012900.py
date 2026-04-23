def _update_qconfig_for_fusion(model: GraphModule, qconfig_mapping: QConfigMapping):
    """
    Update the QConfigMapping to account for fused modules such as LinearReLU.
    This assumes the QConfigMapping's attributes have already been converted to OrderedDicts.
    """
    object_type_dict = qconfig_mapping.object_type_qconfigs
    if len(object_type_dict) == 0:
        return qconfig_mapping

    modules = dict(model.named_modules())

    for node in model.graph.nodes:
        if node.op == "call_module" and node.target in modules:
            maybe_fused_module = modules[str(node.target)]
            if not isinstance(maybe_fused_module, _FusedModule):
                continue

            ops = list(maybe_fused_module._modules.values())
            fused_qconfig = object_type_dict.get(type(ops[0]), None)

            # Raise an error if the modules in the fused module have
            # different qconfigs specified in the qconfig_dict
            # TODO: currently it only works for modules,
            # need to make this work for torch.nn.functional.relu
            # TODO: currently it only works for object_type configurations,
            # ideally it should work for different types of configurations,
            # maybe we want to redesign this part
            for op in ops[1:]:
                if not qconfig_equals(
                    object_type_dict.get(type(op), None), fused_qconfig
                ):
                    raise LookupError(
                        "During fusion, we need to specify the same "
                        + f"qconfigs for all module types in {type(maybe_fused_module)} "
                        + f"offending type: {type(op)}"
                    )

            if fused_qconfig is not None:
                object_type_dict[type(maybe_fused_module)] = fused_qconfig