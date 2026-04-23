def _traverse_obj(self, obj, func):
        if isinstance(obj, (tuple, list)):
            return type(obj)(self._traverse_obj(o, func) for o in obj)
        elif isgenerator(obj):
            return tuple(self._traverse_obj(o, func) for o in obj)
        elif isinstance(obj, dict):
            return {name: self._traverse_obj(o, func) for name, o in obj.items()}
        elif isinstance(obj, (torch.Tensor, torch.nn.Parameter)):
            return func(obj)
        else:
            return obj