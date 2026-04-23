def __torch_function__(
        self,
        func: OpOverload,
        types: tuple[torch._C._TensorMeta, ...],
        args: tuple[object, ...] = (),
        kwargs: dict[str, object] | None = None,
    ) -> object:
        if func is torch.Tensor.__getitem__:
            tensor_to_index = args[0]
            assert isinstance(tensor_to_index, torch.Tensor)
            index_args = pytree.tree_leaves(args[1])
            if all(isinstance(x, (torch.Tensor, int)) for x in index_args):
                converted_indices = [
                    torch.tensor(x, dtype=torch.int64, device=tensor_to_index.device)
                    if isinstance(x, int)
                    else x
                    for x in index_args
                ]
                return mod_index(tensor_to_index, converted_indices)
        return func(*args, **(kwargs or {}))