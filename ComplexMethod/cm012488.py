def infer_arg_by_inputs(raw_keys, raw_args, idx, reused_args):
                """We try to infer raw_arg (i.e. raw_args[idx]) from remaining raw_args.
                This is particularly useful for jagged cases, where the dimension is often
                being passed in as an input."""

                target_arg = raw_args[idx]
                if target_arg in reused_args:
                    return True

                for i, (raw_key, raw_arg) in enumerate(zip(raw_keys, raw_args)):
                    if i == idx or not isinstance(raw_arg, IRNode):
                        continue

                    triton_input = ""
                    if autotune_args and raw_key in autotune_args:
                        triton_input = self.get_autotuning_input_name(  # type: ignore[attr-defined]
                            autotune_args[raw_key]
                        )
                    if triton_input == "":
                        continue

                    try:
                        layout = raw_arg.get_layout()
                        for dim, s in enumerate(layout.size):
                            if s == target_arg:
                                reused_args[target_arg] = f"{triton_input}.shape[{dim}]"
                                return True
                    except NotImplementedError:
                        # If layout for this IRNode is not implemented, we could just skip.
                        # Only raise for other Error cases.
                        continue
                return False