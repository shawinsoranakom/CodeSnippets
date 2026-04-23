def heuristic_record_if_in_graph_function(obj, module, name):
        try:
            if hasattr(obj, "__wrapped__"):
                obj = obj.__wrapped__
        except Exception:
            pass
        if isinstance(
            obj,
            (
                types.FunctionType,
                types.BuiltinFunctionType,
                types.MethodDescriptorType,
                types.WrapperDescriptorType,
            ),
        ) or is_special_functions(obj):
            torch_name_rule_map[f"{module.__name__}.{name}"] = (
                TorchInGraphFunctionVariable
            )
            if c_binding_only:
                if not hasattr(obj, "__code__"):
                    c_binding_in_graph_functions.add(obj)
            else:
                if hasattr(obj, "__code__"):
                    non_c_binding_in_graph_functions.add(obj)
                else:
                    c_binding_in_graph_functions.add(obj)