def inner(fn: Callable[_P, _T]) -> Callable[_P, _T]:
            if inspect.isclass(k) and (
                issubclass(k, TorchDispatchMode) or issubclass(k, torch.Tensor)
            ):
                if k in self.python_key_table:
                    raise AssertionError(f"{k} already registered in python_key_table")
                # TODO(voz): Should we replace setting DispatchKey.Python entirely with setting mode keys?
                self.python_key_table[k] = fn
                self._dispatch_cache.clear()
                return fn

            if isinstance(k, TransformType):
                if k in self.functorch_table:
                    raise AssertionError(f"{k} already registered in functorch_table")
                self.functorch_table[k] = fn
                return fn

            if not isinstance(k, DispatchKey):
                raise AssertionError(f"expected DispatchKey, got {type(k)}")
            if k == DispatchKey.Python:
                raise AssertionError(
                    "Please register a mode for the DispatchKey.Python key instead."
                )

            if k in self.py_kernels:
                raise RuntimeError(
                    f"Trying to override a python impl for {k} on operator {self.name()}"
                )
            self.py_kernels[k] = fn
            self._dispatch_cache.clear()
            return fn