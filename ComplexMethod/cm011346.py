def _iterate_state_dict(
    iter_object: Any,
    dtensor_func: Callable,
    sharded_tensor_func: Callable,
    tensor_func: Callable,
):
    """
    Iterate through the state dict, applying the given functions to each tensor type
    and update the state dict in place.

    Args:
        iter_object (Any): the target state_dict.
        sharded_tensor_func (Callable): the function to apply to ShardedTensor
        dtensor_func (Callable): the function to apply to DTensor
        tensor_func (Callable): the function to apply to Tensor

    # TODO: let state_dict_util._iterate_state_dict() to support in place option
    so we don't need to have two versions of _iterate_state_dict.
    """

    if isinstance(iter_object, DTensor):
        return dtensor_func(iter_object)
    elif isinstance(iter_object, ShardedTensor):
        return sharded_tensor_func(iter_object)
    elif isinstance(iter_object, torch.Tensor):
        return tensor_func(iter_object)
    elif (
        isinstance(iter_object, (int, float, str, bytes, io.BytesIO))
        or iter_object is None
    ):
        return iter_object
    elif isinstance(iter_object, dict):
        for key, value in iter_object.items():
            iter_object[key] = _iterate_state_dict(
                value, dtensor_func, sharded_tensor_func, tensor_func
            )
        return iter_object
    elif isinstance(iter_object, (list, tuple)):
        ret = [
            _iterate_state_dict(v, dtensor_func, sharded_tensor_func, tensor_func)
            for v in iter_object
        ]
        if isinstance(iter_object, tuple):
            ret = tuple(ret)  # type: ignore[assignment]
        return ret