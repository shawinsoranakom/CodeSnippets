def from_yaml_dict(
        op_name: str, op_info: dict[str, object]
    ) -> SelectiveBuildOperator:
        allowed_keys = {
            "name",
            "is_root_operator",
            "is_used_for_training",
            "include_all_overloads",
            "debug_info",
        }

        if len(set(op_info.keys()) - allowed_keys) > 0:
            raise Exception(  # noqa: TRY002
                "Got unexpected top level keys: {}".format(
                    ",".join(set(op_info.keys()) - allowed_keys),
                )
            )

        if "name" in op_info:
            if op_name != op_info["name"]:
                raise AssertionError(
                    f"op_name mismatch: {op_name} != {op_info['name']}"
                )

        is_root_operator = op_info.get("is_root_operator", True)
        if not isinstance(is_root_operator, bool):
            raise AssertionError(
                f"Expected 'is_root_operator' to be bool, got {type(is_root_operator)}"
            )

        is_used_for_training = op_info.get("is_used_for_training", True)
        if not isinstance(is_used_for_training, bool):
            raise AssertionError(
                f"Expected 'is_used_for_training' to be bool, got {type(is_used_for_training)}"
            )

        include_all_overloads = op_info.get("include_all_overloads", True)
        if not isinstance(include_all_overloads, bool):
            raise AssertionError(
                f"Expected 'include_all_overloads' to be bool, got {type(include_all_overloads)}"
            )

        debug_info: tuple[str, ...] | None = None
        if "debug_info" in op_info:
            di_list = op_info["debug_info"]
            if not isinstance(di_list, list):
                raise AssertionError(
                    f"Expected 'debug_info' to be list, got {type(di_list)}"
                )
            debug_info = tuple(str(x) for x in di_list)

        return SelectiveBuildOperator(
            name=op_name,
            is_root_operator=is_root_operator,
            is_used_for_training=is_used_for_training,
            include_all_overloads=include_all_overloads,
            _debug_info=debug_info,
        )