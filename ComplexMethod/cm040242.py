def map_tensors(tensors):
        if (
            isinstance(tensors, list)
            and len(tensors) == 3
            and isinstance(tensors[0], str)
        ):
            # Leaf
            return get_tensor(*tensors)
        if isinstance(tensors, dict):
            return {k: map_tensors(v) for k, v in tensors.items()}
        if isinstance(tensors, tuple):
            return tuple([map_tensors(v) for v in tensors])
        return [map_tensors(v) for v in tensors]