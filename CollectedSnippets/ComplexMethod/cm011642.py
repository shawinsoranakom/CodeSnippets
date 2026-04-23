def broadcast_shapes_for_args(args: Sequence[ShapeArg]) -> BlockShapeType:
    result_shape: BlockShapeType = None

    for arg in args:
        if hasattr(arg, "shape"):
            shape = arg.shape
            if shape is None:
                return None
            elif result_shape is None:
                result_shape = tuple(shape)
            else:
                result_shape = get_broadcasted_shape(result_shape, tuple(shape))
        elif isinstance(arg, (int, float)):
            if result_shape is None:
                result_shape = ()
        elif isinstance(arg, torch.dtype):
            continue
        else:
            from torch._inductor.loop_body import LoopBody, LoopBodyBlock

            if isinstance(arg, (LoopBodyBlock, LoopBody, OpsValue)):
                # TODO: fix me
                return None
            raise TypeError(f"Unknown type: {type(arg)}")

    return result_shape