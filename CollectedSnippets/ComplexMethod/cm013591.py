def _get_node_label(
            self,
            module: torch.fx.GraphModule,
            node: torch.fx.Node,
            skip_node_names_in_args: bool,
            parse_stack_trace: bool,
        ) -> str:
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

            label = "{" + f"name=%{node.name}|op_code={node.op}\n"

            if node.op == "call_module":
                leaf_module = self._get_leaf_node(module, node)
                label += r"\n" + self._typename(leaf_module) + r"\n|"
                extra = ""
                if hasattr(leaf_module, "__constants__"):
                    extra = r"\n".join(
                        [
                            f"{c}: {getattr(leaf_module, c)}"
                            for c in leaf_module.__constants__  # type: ignore[union-attr]
                        ]  # type: ignore[union-attr]
                    )
                label += extra + r"\n"
            else:
                label += f"|target={self._typename(node.target)}" + r"\n"
                if self.normalize_args:
                    try:
                        args, kwargs = normalize_function(  # type: ignore[misc]
                            node.target,  # type: ignore[arg-type]
                            node.args,  # type: ignore[arg-type]
                            node.kwargs,
                            normalize_to_only_use_kwargs=True,
                        )
                    except Exception:
                        # Fallback to not normalizing if there's an exception.
                        # Some functions need overloads specified to normalize.
                        args, kwargs = node.args, node.kwargs
                else:
                    args, kwargs = node.args, node.kwargs
                if len(args) > 0:
                    label += _get_str_for_args_kwargs(args)
                if len(kwargs) > 0:
                    label += _get_str_for_args_kwargs(kwargs)
                label += f"|num_users={len(node.users)}" + r"\n"

            tensor_meta = node.meta.get("tensor_meta")
            label += self._tensor_meta_to_label(tensor_meta)

            # for original fx graph
            # print buf=buf0, n_origin=6
            buf_meta = node.meta.get("buf_meta", None)
            if buf_meta is not None:
                label += f"|buf={buf_meta.name}" + r"\n"
                label += f"|n_origin={buf_meta.n_origin}" + r"\n"

            # for original fx graph
            # print file:lineno code
            if parse_stack_trace and node.stack_trace is not None:
                parsed_stack_trace = _parse_stack_trace(node.stack_trace)
                if parsed_stack_trace is not None:
                    fname = self._shorten_file_name(parsed_stack_trace.file)
                    label += (
                        f"|file={fname}:{parsed_stack_trace.lineno} {parsed_stack_trace.code}"
                        + r"\n"
                    )

            return label + "}"