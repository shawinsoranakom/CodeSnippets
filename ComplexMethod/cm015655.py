def __torch_dispatch__(cls, func, types, args, kwargs):
        if kwargs is None:
            kwargs = {}
        biggest_constant = max(
            [
                x.constant
                for x in pytree.tree_flatten(args)[0]
                if isinstance(x, CtxSubclassTensor)
            ]
        )
        args_a = pytree.tree_map(
            lambda x: x.a if isinstance(x, CtxSubclassTensor) else x, args
        )
        kwargs_a = pytree.tree_map(
            lambda x: x.a if isinstance(x, CtxSubclassTensor) else x, kwargs
        )
        out_a = func(*args_a, **kwargs_a)
        out = pytree.tree_map(
            lambda x: (
                CtxSubclassTensor(x, biggest_constant)
                if isinstance(x, torch.Tensor)
                else x
            ),
            out_a,
        )

        if func == torch.ops.aten.mul.Tensor:
            out = out + out.constant

        return return_and_correct_aliasing(func, args, kwargs, out)