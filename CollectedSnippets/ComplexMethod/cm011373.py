def _reconstruct(
        self,
        x,
        memo,
        func,
        args,
        state=None,
        listiter=None,
        dictiter=None,
        non_blocking=False,
    ):
        deep = memo is not None
        if deep and args:
            args = tuple(
                self.deepcopy_with_tensor_offload(arg, memo, non_blocking=non_blocking)
                for arg in args
            )
        y = func(*args)
        if deep:
            memo[id(x)] = y

        if state is not None:
            if deep:
                state = self.deepcopy_with_tensor_offload(
                    state, memo, non_blocking=non_blocking
                )
            if hasattr(y, "__setstate__"):
                y.__setstate__(state)
            else:
                if isinstance(state, tuple) and len(state) == 2:
                    state, slotstate = state
                else:
                    slotstate = None
                if state is not None:
                    y.__dict__.update(state)
                if slotstate is not None:
                    for key, value in slotstate.items():
                        setattr(y, key, value)

        if listiter is not None:
            if deep:
                for item in listiter:
                    item = self.deepcopy_with_tensor_offload(
                        item, memo, non_blocking=non_blocking
                    )
                    y.append(item)
            else:
                for item in listiter:
                    y.append(item)
        if dictiter is not None:
            if deep:
                for key, value in dictiter:
                    key = self.deepcopy_with_tensor_offload(
                        key, memo, non_blocking=non_blocking
                    )
                    value = self.deepcopy_with_tensor_offload(
                        value, memo, non_blocking=non_blocking
                    )
                    y[key] = value
            else:
                for key, value in dictiter:
                    y[key] = value
        return y