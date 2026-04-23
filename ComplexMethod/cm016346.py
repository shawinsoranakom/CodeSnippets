def fill_output(output: dict[str, object], options: Namespace) -> None:
    """Populate the output dict with the information required to serialize
    the YAML file used for selective build.
    """
    dept_graph = load_op_dep_graph(options.dep_graph_yaml_path)

    model_versions = (
        options.model_versions.split(",") if options.model_versions is not None else []
    )
    model_assets = (
        options.model_assets.split(",") if options.model_assets is not None else None
    )

    all_models_yaml = []
    if options.models_yaml_path:
        for yaml_path in options.models_yaml_path:
            with open(yaml_path, "rb") as f:
                all_models_yaml.append(yaml.safe_load(f))

    model_filter_func = make_filter_from_options(
        options.model_name, model_versions, model_assets, options.model_backends
    )

    selected_models_yaml = list(filter(model_filter_func, all_models_yaml))

    verify_all_specified_present(
        model_assets=model_assets,
        model_versions=model_versions,
        selected_models_yaml=selected_models_yaml,
        rule_name=options.rule_name,
        model_name=options.model_name,
        new_style_rule=is_new_style_rule(options.model_name, options.model_versions),
    )

    create_debug_info_from_selected_models(
        output,
        selected_models_yaml,
        is_new_style_rule(options.model_name, options.model_versions),
    )

    # initialize variables for static build from the pt_operator_library rule
    if options.root_ops is not None:
        static_root_ops = set(filter(lambda x: len(x) > 0, options.root_ops.split(",")))
    else:
        static_root_ops = set()

    static_training_root_ops = set(
        filter(
            lambda x: len(x) > 0,
            (options.training_root_ops or "").split(","),
        )
    )
    if len(static_training_root_ops) > 0:
        static_root_ops = static_root_ops | static_training_root_ops
    # end if

    root_ops_unexpand = set()
    traced_ops = set()
    training_root_ops_unexpand = set()
    traced_training_ops = set()
    all_kernel_metadata = []
    all_custom_classes = set()
    all_build_features = set()

    # Go through each yaml file and retrieve operator information.
    for model_info in selected_models_yaml:
        if "traced_operators" not in model_info:
            # If this YAML file doesn't specify any traced operators, then it is using
            # the static analysis selective build approach of finding transitively
            # used operators, and we should update root_ops with the set of root
            # operators, all of whose overloads must be included. In addition, these
            # root_ops will be further expanded using the transitive closure of
            # operator dependencies.
            static_root_ops = static_root_ops | set(model_info["root_operators"])
        else:
            # If this YAML file specifies traced operators, then it is using
            # the tracing based selective build approach of finding used
            # operators, and we should update root_ops_unexpand with the set of root
            # operators whose overloads don't need to be included. In addition, these
            # root_ops_unexpand will NOT be further expanded. If the train flag is
            # set then the ops will be used for training, so we put them in a separate
            # set
            if model_info["train"]:
                training_root_ops_unexpand = training_root_ops_unexpand | set(
                    model_info["root_operators"]
                )
                traced_training_ops = traced_training_ops | set(
                    model_info["traced_operators"]
                )
            else:
                root_ops_unexpand = root_ops_unexpand | set(
                    model_info["root_operators"]
                )
                traced_ops = traced_ops | set(model_info["traced_operators"])

        if "kernel_metadata" in model_info:
            all_kernel_metadata.append(model_info["kernel_metadata"])

        if "custom_classes" in model_info:
            all_custom_classes = all_custom_classes | set(model_info["custom_classes"])

        if "build_features" in model_info:
            all_build_features = all_build_features | set(model_info["build_features"])

    # This following section on transitive closure is relevant to static build only
    # pyrefly: ignore [bad-argument-type]
    canonical_root_ops = canonical_opnames(static_root_ops)
    # If no canonical_root_ops exist, don't compute the transitive closure
    # otherwise, we will include __BASE__ and __ROOT__ ops and mark them as required
    # for inference.
    if len(canonical_root_ops) > 0:
        closure_op_list = gen_transitive_closure(dept_graph, canonical_root_ops)
    else:
        closure_op_list = set()

    # pyrefly: ignore [bad-argument-type]
    canonical_training_root_ops = canonical_opnames(static_training_root_ops)
    # If no canonical_training_root_ops exist, don't compute the transitive closure
    # otherwise, we will include __BASE__ and __ROOT__ ops and mark them as required
    # for training.
    if len(canonical_training_root_ops) > 0:
        closure_training_op_list = gen_transitive_closure(
            dept_graph, canonical_training_root_ops, train=True
        )
    else:
        closure_training_op_list = set()

    # bucketed_ops holds sets of operators that correspond to specific semantic buckets. For
    # example:
    #
    # 1. Root Operators not used for training w/o full overload inclusion
    # 2. Root Operators not used for training w/ full overload inclusion
    # 3. Root Operators used for training w/o full overload inclusion
    # 4. Root Operators used for training w/ full overload inclusion
    # 5. Non-root Operators not used for training w/o full overload inclusion
    # etc...
    #
    # Basically for each of the 3 boolean conditional, there are 2
    # options (True/False).
    #
    bucketed_ops = []

    # START STATIC BUILD OPS
    static_root_ops_bucket = {}
    for op_name in static_root_ops:
        op = SelectiveBuildOperator.from_yaml_dict(
            op_name,
            {
                "is_root_operator": True,
                "is_used_for_training": False,
                "include_all_overloads": not options.not_include_all_overloads_static_root_ops,
                "debug_info": [options.model_name],
            },
        )
        static_root_ops_bucket[op_name] = op
    bucketed_ops.append(static_root_ops_bucket)

    closure_ops_bucket = {}
    for op_name in closure_op_list:
        op = SelectiveBuildOperator.from_yaml_dict(
            op_name,
            {
                "is_root_operator": False,
                "is_used_for_training": False,
                "include_all_overloads": not options.not_include_all_overloads_closure_ops,
                "debug_info": [options.model_name],
            },
        )
        closure_ops_bucket[op_name] = op
    bucketed_ops.append(closure_ops_bucket)

    static_training_root_ops_bucket = {}
    for op_name in static_training_root_ops:
        op = SelectiveBuildOperator.from_yaml_dict(
            op_name,
            {
                "is_root_operator": True,
                "is_used_for_training": True,
                "include_all_overloads": True,
                "debug_info": [options.model_name],
            },
        )
        static_training_root_ops_bucket[op_name] = op
    bucketed_ops.append(static_training_root_ops_bucket)

    closure_training_ops_bucket = {}
    for op_name in closure_training_op_list:
        op = SelectiveBuildOperator.from_yaml_dict(
            op_name,
            {
                "is_root_operator": False,
                "is_used_for_training": True,
                "include_all_overloads": True,
                "debug_info": [options.model_name],
            },
        )
        closure_training_ops_bucket[op_name] = op
    bucketed_ops.append(closure_training_ops_bucket)
    # END STATIC BUILD OPS

    # START TRACING BASED BUILD OPS
    root_ops_unexpand_bucket = {}
    for op_name in root_ops_unexpand:
        op = SelectiveBuildOperator.from_yaml_dict(
            op_name,
            {
                "is_root_operator": True,
                "is_used_for_training": False,
                "include_all_overloads": False,
                "debug_info": [options.model_name],
            },
        )
        root_ops_unexpand_bucket[op_name] = op
    bucketed_ops.append(root_ops_unexpand_bucket)

    traced_ops_bucket = {}
    for op_name in traced_ops:
        op = SelectiveBuildOperator.from_yaml_dict(
            op_name,
            {
                "is_root_operator": False,
                "is_used_for_training": False,
                "include_all_overloads": False,
                "debug_info": [options.model_name],
            },
        )
        traced_ops_bucket[op_name] = op
    bucketed_ops.append(traced_ops_bucket)

    training_root_ops_unexpand_bucket = {}
    for op_name in training_root_ops_unexpand:
        op = SelectiveBuildOperator.from_yaml_dict(
            op_name,
            {
                "is_root_operator": True,
                "is_used_for_training": True,
                "include_all_overloads": False,
                "debug_info": [options.model_name],
            },
        )
        training_root_ops_unexpand_bucket[op_name] = op
    bucketed_ops.append(training_root_ops_unexpand_bucket)

    traced_training_ops_bucket = {}
    for op_name in traced_training_ops:
        op = SelectiveBuildOperator.from_yaml_dict(
            op_name,
            {
                "is_root_operator": False,
                "is_used_for_training": True,
                "include_all_overloads": False,
                "debug_info": [options.model_name],
            },
        )
        traced_training_ops_bucket[op_name] = op
    bucketed_ops.append(traced_training_ops_bucket)
    # END TRACING BASED BUILD OPS

    # Merge dictionaries together to remove op duplication
    operators: dict[str, SelectiveBuildOperator] = {}
    for ops_dict in bucketed_ops:
        operators = merge_operator_dicts(operators, ops_dict)

    # Loop over all operators, and if any of the them specifies that
    # all overloads need to be included, then set include_all_non_op_selectives
    # to True, since it indicates that this operator list came from something
    # other than a traced operator list.
    include_all_non_op_selectives = False
    for op_name, op_info in operators.items():
        include_all_non_op_selectives = (
            include_all_non_op_selectives or op_info.include_all_overloads
        )

    operators_as_dict = {}
    for k, v in operators.items():
        operators_as_dict[k] = v.to_dict()

    output["operators"] = operators_as_dict

    output["custom_classes"] = all_custom_classes

    output["build_features"] = all_build_features

    output["include_all_non_op_selectives"] = include_all_non_op_selectives
    if len(all_kernel_metadata) > 0:
        kernel_metadata = {}
        for kt in all_kernel_metadata:
            kernel_metadata = merge_kernel_metadata(kernel_metadata, kt)
        output["kernel_metadata"] = kernel_metadata