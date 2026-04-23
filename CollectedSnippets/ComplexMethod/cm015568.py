def deep_compare(self, obj1: Any, obj2: Any) -> bool:
        if isinstance(obj1, dict) and isinstance(obj2, dict):
            if obj1.keys() != obj2.keys():
                return False
            return all(self.deep_compare(obj1[key], obj2[key]) for key in obj1)
        elif isinstance(obj1, (list, tuple)) and isinstance(obj2, (list, tuple)):
            if len(obj1) != len(obj2):
                return False
            return all(
                self.deep_compare(item1, item2) for item1, item2 in zip(obj1, obj2)
            )
        elif isinstance(obj1, torch.Tensor) and isinstance(obj2, torch.Tensor):
            return torch.equal(obj1, obj2)
        else:
            return obj1 == obj2