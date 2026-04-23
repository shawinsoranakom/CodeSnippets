def load_derivatives(
    derivatives_yaml_path: str, native_yaml_path: str, tags_yaml_path: str
) -> DerivativeRet:
    # Do some caching as this is a deterministic function
    global _GLOBAL_LOAD_DERIVATIVE_CACHE
    key = (derivatives_yaml_path, native_yaml_path)
    if key not in _GLOBAL_LOAD_DERIVATIVE_CACHE:
        with open(derivatives_yaml_path) as f:
            definitions = yaml.load(f, Loader=YamlLoader)

        funcs = parse_native_yaml(native_yaml_path, tags_yaml_path).native_functions
        # From the parsed native functions, separate out the (generated) view_copy functions,
        # so we can generate derivatives for them separately.
        native_functions_with_view_groups = get_grouped_by_view_native_functions(funcs)
        native_functions = concatMap(
            lambda g: [g]
            if isinstance(g, NativeFunction)
            else list(g.functions(include_copy=True)),
            native_functions_with_view_groups,
        )
        view_groups = [
            g
            for g in native_functions_with_view_groups
            if isinstance(g, NativeFunctionsViewGroup)
        ]

        # What's the difference between function schema v.s. signature?
        # function schema is the complete declaration including mutability annotation / default value and etc.
        # signature is the canonical schema for a group of functions (in-place/out/functional variants)
        # that are semantically related.
        functions_by_signature: dict[FunctionSchema, list[NativeFunction]] = (
            defaultdict(list)
        )
        functions_by_schema: dict[str, NativeFunction] = {}
        for function in native_functions:
            functions_by_signature[function.func.signature()].append(function)
            if str(function.func) in functions_by_schema:
                raise AssertionError(f"Duplicate function schema: {str(function.func)}")
            functions_by_schema[str(function.func)] = function

        # Keep track of how many of which ops we've seen so we can
        # disambiguate them with a numeric suffix.
        op_counter = Counter[str]()

        # infos is a dict that maps FunctionSchema -> a dict of per dispatch key DifferentiabilityInfos
        # this is useful because in tools/autograd/gen_autograd.py:match_differentiability_info
        # we ultimately need to categorize the DifferentiabilityInfos by FunctionSchema
        infos: dict[FunctionSchema, dict[str, DifferentiabilityInfo]] = {}
        used_dispatch_keys: set[str] = set()
        for defn_dict in definitions:
            # Ensure that the old derivatives.yaml schema with no dispatch key can be loaded.
            if "dispatch" not in defn_dict:
                specification = defn_dict.pop("name")
                output_differentiability = defn_dict.pop(
                    "output_differentiability", None
                )
                defn_dict = {"name": specification, "dispatch": {"Default": defn_dict}}
                if output_differentiability:
                    defn_dict["output_differentiability"] = output_differentiability
            name, per_dispatch_diffinfos = create_differentiability_info(
                defn_dict,
                functions_by_signature,
                functions_by_schema,
                op_counter,
                used_dispatch_keys,
            )
            infos[name] = per_dispatch_diffinfos

        add_view_copy_derivatives(infos, view_groups)

        # cache both loaded infos as well as a set of all the dispatch_keys/aliases
        # that appear in derivatives.yaml. used_dispatch_keys is useful for generating
        # VariableType.cpp where we need a TORCH_LIBRARY_IMPL for every autograd dispatch key used
        _GLOBAL_LOAD_DERIVATIVE_CACHE[key] = infos, used_dispatch_keys

    return _GLOBAL_LOAD_DERIVATIVE_CACHE[key]