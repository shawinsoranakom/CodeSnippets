def from_yaml_dict(data: dict[str, object]) -> SelectiveBuilder:
        valid_top_level_keys = {
            "include_all_non_op_selectives",
            "include_all_operators",
            "debug_info",
            "operators",
            "kernel_metadata",
            "et_kernel_metadata",
            "custom_classes",
            "build_features",
        }
        top_level_keys = set(data.keys())
        if len(top_level_keys - valid_top_level_keys) > 0:
            raise Exception(  # noqa: TRY002
                "Got unexpected top level keys: {}".format(
                    ",".join(top_level_keys - valid_top_level_keys),
                )
            )
        include_all_operators = data.get("include_all_operators", False)
        if not isinstance(include_all_operators, bool):
            raise AssertionError(
                f"Expected 'include_all_operators' to be bool, got {type(include_all_operators)}"
            )

        debug_info = None
        if "debug_info" in data:
            di_list = data["debug_info"]
            if not isinstance(di_list, list):
                raise AssertionError(
                    f"Expected 'debug_info' to be list, got {type(di_list)}"
                )

            debug_info = tuple(str(x) for x in di_list)

        operators = {}
        operators_dict = data.get("operators", {})
        if not isinstance(operators_dict, dict):
            raise AssertionError(
                f"Expected 'operators' to be dict, got {type(operators_dict)}"
            )

        for k, v in operators_dict.items():
            operators[k] = SelectiveBuildOperator.from_yaml_dict(k, v)

        kernel_metadata = {}
        kernel_metadata_dict = data.get("kernel_metadata", {})
        if not isinstance(kernel_metadata_dict, dict):
            raise AssertionError(
                f"Expected 'kernel_metadata' to be dict, got {type(kernel_metadata_dict)}"
            )

        for k, v in kernel_metadata_dict.items():
            kernel_metadata[str(k)] = [str(dtype) for dtype in v]

        et_kernel_metadata = data.get("et_kernel_metadata", {})
        if not isinstance(et_kernel_metadata, dict):
            raise AssertionError(
                f"Expected 'et_kernel_metadata' to be dict, got {type(et_kernel_metadata)}"
            )

        custom_classes = data.get("custom_classes", [])
        if not isinstance(custom_classes, Iterable):
            raise AssertionError(
                f"Expected 'custom_classes' to be Iterable, got {type(custom_classes)}"
            )
        custom_classes = set(custom_classes)

        build_features = data.get("build_features", [])
        if not isinstance(build_features, Iterable):
            raise AssertionError(
                f"Expected 'build_features' to be Iterable, got {type(build_features)}"
            )
        build_features = set(build_features)

        include_all_non_op_selectives = data.get("include_all_non_op_selectives", False)
        if not isinstance(include_all_non_op_selectives, bool):
            raise AssertionError(
                f"Expected 'include_all_non_op_selectives' to be bool, "
                f"got {type(include_all_non_op_selectives)}"
            )

        return SelectiveBuilder(
            include_all_operators,
            debug_info,
            operators,
            kernel_metadata,
            et_kernel_metadata,
            custom_classes,  # type: ignore[arg-type]
            build_features,  # type: ignore[arg-type]
            include_all_non_op_selectives,
        )