def _override(self, func, args, kwargs):
        if torch.distributed.is_available():
            from torch.distributed._functional_collectives import (
                REDUCE_OP_TO_STR,
                traceable_collective_remaps,
            )

            if func in traceable_collective_remaps:
                # Redirect to a corresponding functional collective, following Dynamo.
                # See torch/distributed/_functional_collectives.py for details.
                # The following is an adaptation of CollectiveFunctionRewriteVariable.
                mapped_func = traceable_collective_remaps[func]
                signature = inspect.signature(func)
                kwargs = dict(signature.bind(*args, **kwargs).arguments)
                args = ()
                if func in (
                    torch.distributed.all_reduce,
                    torch.distributed.reduce_scatter_tensor,
                    torch.distributed._reduce_scatter_base,
                ):
                    if "op" in kwargs:
                        kwargs["op"] = REDUCE_OP_TO_STR[kwargs["op"]]
                return mapped_func, args, kwargs
        if func is torch.tensor:
            # Redirect to Python implementation of torch.tensor for data with symints.
            # NOTE(avik): We don't unconditionally redirect to this implementation
            # because it has some known incompletenesses, e.g., it doesn't support
            # empty data. See https://github.com/pytorch/pytorch/issues/143216
            if any(
                isinstance(a, (torch.SymInt, torch.SymFloat, torch.SymBool))
                for a in pytree.tree_flatten(args[0])[0]
            ):
                return torch._refs.tensor, args, kwargs
        if func.__name__ == "__getitem__" and isinstance(args[0], torch.Tensor):

            def rewrite(dim, item):
                # Redirect to torch.select for indexing.
                if item is None:
                    return dim + 1, (torch.unsqueeze, [dim])
                if isinstance(item, (int, torch.SymInt)):
                    return dim, (torch.select, [dim, item])
                # Redirect to torch.ops.aten.slice for slicing.
                if isinstance(item, slice):
                    step = item.step or 1
                    if item.start is None and item.stop is None and step == 1:
                        # no-op
                        return dim + 1, (lambda t: t, [])
                    return dim + 1, (
                        torch.ops.aten.slice,
                        [dim, item.start, item.stop, step],
                    )
                # Otherwise do nothing.

            items = list(args[1]) if isinstance(args[1], tuple) else [args[1]]

            has_symint = False
            index_ellipsis = None
            t = args[0]
            n_none_slices = t.ndim + 1
            for i, item in enumerate(items):
                if isinstance(item, torch.SymInt) or (
                    isinstance(item, slice)
                    and any(
                        isinstance(s, torch.SymInt)
                        for s in (item.start, item.stop, item.step)
                    )
                ):
                    has_symint = True
                if item is Ellipsis:
                    index_ellipsis = i
                if item is not None:
                    n_none_slices -= 1

            # only rewrite when there are symints
            if has_symint:
                if index_ellipsis is not None:
                    none_slices = [slice(None)] * n_none_slices
                    items[index_ellipsis : index_ellipsis + 1] = none_slices

                dim = 0
                # Sequence rewrites.
                sequence = []
                for item in items:
                    if (r := rewrite(dim, item)) is None:
                        return func, args, kwargs
                    dim, call_spec = r
                    sequence.append(call_spec)

                def run():
                    # Run sequence.
                    # pyrefly: ignore [bad-index, index-error]
                    t = args[0]
                    for _method, _args in sequence:
                        t = _method(t, *_args)
                    return t

                return run, [], {}

        return func, args, kwargs