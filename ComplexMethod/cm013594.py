def _get_str_for_args_kwargs(arg: tuple[Any, ...] | dict[str, Any]) -> str:
                if isinstance(arg, tuple):
                    prefix, suffix = r"|args=(\l", r",\n)\l"
                    arg_strs_list = [_format_arg(a, max_list_len=8) for a in arg]
                elif isinstance(arg, dict):
                    prefix, suffix = r"|kwargs={\l", r",\n}\l"
                    arg_strs_list = [
                        f"{k}: {_format_arg(v, max_list_len=8)}" for k, v in arg.items()
                    ]
                else:  # Fall back to nothing in unexpected case.
                    return ""

                # Strip out node names if requested.
                if skip_node_names_in_args:
                    arg_strs_list = [a for a in arg_strs_list if "%" not in a]
                if len(arg_strs_list) == 0:
                    return ""
                arg_strs = prefix + r",\n".join(arg_strs_list) + suffix
                if len(arg_strs_list) == 1:
                    arg_strs = arg_strs.replace(r"\l", "").replace(r"\n", "")
                return arg_strs.replace("{", r"\{").replace("}", r"\}")