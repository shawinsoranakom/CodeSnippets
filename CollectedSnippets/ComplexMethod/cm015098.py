def __torch_dispatch__(self, func, types, args=(), kwargs=None):
        out = func(*args, **(kwargs or {}))
        parents = self._tracker.parents - {"Global"}
        fqn = max(parents, key=len) if parents else "Global"
        op_name = func.__name__ if hasattr(func, "__name__") else str(func)
        key = (fqn, func)
        count = self._func_counter[key]
        self._func_counter[key] += 1
        multi_output = (
            isinstance(out, (tuple, list))
            and sum(isinstance(o, torch.Tensor) for o in out) > 1
        )
        if isinstance(out, torch.Tensor):
            self.names[out] = f"{fqn}_{op_name}_{count}"
        elif isinstance(out, (tuple, list)):
            for i, o in enumerate(out):
                if isinstance(o, torch.Tensor):
                    name = f"{fqn}_{op_name}_{count}"
                    if multi_output:
                        name += f"_{i}"
                    self.names[o] = name
        return out