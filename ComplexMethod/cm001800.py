def _get_leaf_tensors(obj) -> dict[str, torch.Tensor]:
            if _is_pure_python_object(obj):
                return {}
            elif isinstance(obj, torch.Tensor):
                return {"": obj}
            elif isinstance(obj, (list, tuple, set)):
                return _get_leaf_tensors(dict(enumerate(obj)))
            elif isinstance(obj, dict):
                leaf_tensors = {}
                for key, value in obj.items():
                    for sub_key, tensor in _get_leaf_tensors(value).items():
                        full_key = f"{key}.{sub_key}" if sub_key else str(key)
                        leaf_tensors[full_key] = tensor
                return leaf_tensors
            else:
                raise ValueError(f"Unexpected object type: {type(obj)}")