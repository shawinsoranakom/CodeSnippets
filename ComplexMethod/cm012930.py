def get_normalized_nth_input(node: Node, gm: GraphModule, idx: int) -> Node:
    """
    Given a node, gets the n'th input to that node, normalizing
    args and kwargs to the best of its ability.
    """
    try:
        norm_args_and_kwargs = node.normalized_arguments(
            gm, normalize_to_only_use_kwargs=True
        )
        if norm_args_and_kwargs is not None:
            norm_args, norm_kwargs = norm_args_and_kwargs
            if len(norm_args) + len(norm_kwargs) <= idx:
                raise AssertionError(
                    f"Index {idx} out of range: total = {len(norm_args) + len(norm_kwargs)}"
                )
            if idx < len(norm_args):
                return norm_args[idx]
            else:
                # note: in Python 3.7+ dicts are ordered
                return list(norm_kwargs.values())[idx]
        else:
            if len(node.args) + len(node.kwargs) <= idx:
                raise AssertionError(
                    f"Index {idx} out of range: total = {len(node.args) + len(node.kwargs)}"
                )
            if idx < len(node.args):
                return node.args[idx]  # type: ignore[return-value]
            else:
                kwargs_idx = idx + len(node.args)
                return list(node.kwargs.values())[kwargs_idx]  # type: ignore[return-value]
    except RuntimeError:
        # this RuntimeError happens when node argument normalization
        # requires typehints to proceed, such as for torch.add where
        # either the first, second or both arguments could be tensors
        if len(node.args) + len(node.kwargs) <= idx:
            raise AssertionError(
                f"Index {idx} out of range: total = {len(node.args) + len(node.kwargs)}"
            ) from None
        if idx < len(node.args):
            return node.args[idx]  # type: ignore[return-value]
        else:
            kwargs_idx = idx + len(node.args)
            return list(node.kwargs.values())[kwargs_idx]