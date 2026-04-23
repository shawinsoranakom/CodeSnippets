def auto_dynamic_shapes_from_args(args):  # pyre-ignore
            """
            This function creates dynamic shapes specification with Dim.AUTO
            in all dimensions of all tensors for given argument list.
            """
            if isinstance(args, list):
                return [auto_dynamic_shapes_from_args(arg) for arg in args]
            elif isinstance(args, tuple):
                return tuple(auto_dynamic_shapes_from_args(arg) for arg in args)
            elif isinstance(args, dict):
                return {k: auto_dynamic_shapes_from_args(v) for k, v in args.items()}
            elif isinstance(args, torch.Tensor):
                return {j: Dim.AUTO for j in range(args.dim())}
            else:
                print(f"args type: {type(args)}")
                return None