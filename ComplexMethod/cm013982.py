def has_tensor(obj: object) -> bool:
        """Recursively check if the obj has a tensor"""
        obj_id = id(obj)
        if obj_id in seen_ids:
            return seen_ids[obj_id]
        seen_ids[obj_id] = False

        if isinstance(obj, (torch.Tensor, torch.nn.Module)) or (
            istype(obj, type) and issubclass(obj, torch.nn.Module)
        ):
            seen_ids[obj_id] = True
            return seen_ids[obj_id]
        elif (
            config.trace_numpy
            and np
            and (istype(obj, np.ndarray) or isinstance(obj, np.generic))
        ):
            seen_ids[obj_id] = True
            return seen_ids[obj_id]
        elif istype(obj, (list, tuple)):
            seen_ids[obj_id] = any(has_tensor(v) for v in obj)
            return seen_ids[obj_id]
        elif istype(obj, dict):
            # Some packages like pytest can be updated during runtime. So, make a
            # copy of values to avoid issues like "RuntimeError: dictionary
            # changed size during iteration"
            values = list(obj.values())
            seen_ids[obj_id] = any(has_tensor(v) for v in values)
            return seen_ids[obj_id]
        elif istype(obj, (str, int, float, type(None), bool)):
            seen_ids[obj_id] = False
            return seen_ids[obj_id]
        elif is_namedtuple(obj) and hasattr(obj, "_fields"):
            seen_ids[obj_id] = any(has_tensor(getattr(obj, v)) for v in obj._fields)
            return seen_ids[obj_id]
        else:
            # if config.debug:
            #     print(
            #         f"Assuming that object of type {type(obj)} does not have a tensor"
            #     )
            return False