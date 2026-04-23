def _find_arg_access_count(
        initial_stack: list[Param | Intermediate],
        skip_loads: bool,
    ) -> dict[int, int]:
        """DFS traversal to find argument indices that are accessed (and how many times they are accessed)."""
        access_count = dict()
        stack = initial_stack[:]

        while stack:
            arg = stack.pop()

            if isinstance(arg, Param):
                if arg.idx >= num_args:
                    continue
                if tensor_arg_indices is not None and arg.idx not in tensor_arg_indices:
                    continue
                if arg.idx not in access_count:
                    access_count[arg.idx] = 1
                else:
                    access_count[arg.idx] += 1
            elif isinstance(arg, Intermediate) and not arg.fake():
                for op in ops[arg]:
                    if skip_loads and op.name == "tt.load":
                        continue
                    if op.name in POINTER_ONLY_OPS:
                        stack.append(op.args[0])
                    else:
                        stack.extend(op.args)

        return access_count