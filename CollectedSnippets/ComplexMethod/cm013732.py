def __setattr__(self, name: str, value: Union[Tensor, "Module"]) -> None:
        def remove_from(*dicts_or_sets) -> None:
            for d in dicts_or_sets:
                if name in d:
                    if isinstance(d, dict):
                        del d[name]
                    else:
                        d.discard(name)

        params = self.__dict__.get("_parameters")
        if isinstance(value, Parameter):
            if params is None:
                raise AttributeError(
                    "cannot assign parameters before Module.__init__() call"
                )
            remove_from(
                self.__dict__,
                self._buffers,
                self._modules,
                self._non_persistent_buffers_set,
            )
            self.register_parameter(name, value)
        elif params is not None and name in params:
            if value is not None:
                raise TypeError(
                    f"cannot assign '{torch.typename(value)}' as parameter '{name}' "
                    "(torch.nn.Parameter or None expected)"
                )
            self.register_parameter(name, value)
        else:
            modules = self.__dict__.get("_modules")
            if isinstance(value, Module):
                if modules is None:
                    raise AttributeError(
                        "cannot assign module before Module.__init__() call"
                    )
                remove_from(
                    self.__dict__,
                    self._parameters,
                    self._buffers,
                    self._non_persistent_buffers_set,
                )
                for hook in _global_module_registration_hooks.values():
                    output = hook(self, name, value)
                    if output is not None:
                        value = output
                modules[name] = value
            elif modules is not None and name in modules:
                if value is not None:
                    raise TypeError(
                        f"cannot assign '{torch.typename(value)}' as child module '{name}' "
                        "(torch.nn.Module or None expected)"
                    )
                for hook in _global_module_registration_hooks.values():
                    output = hook(self, name, value)
                    if output is not None:
                        value = output
                modules[name] = value
            else:
                buffers = self.__dict__.get("_buffers")
                if isinstance(value, Buffer) or buffers is not None and name in buffers:
                    if value is not None and not (
                        isinstance(value, torch.Tensor)
                        or hasattr(value, "__torch_function__")
                    ):
                        raise TypeError(
                            f"cannot assign '{torch.typename(value)}' as buffer '{name}' "
                            "(torch.nn.Buffer, torch.Tensor or None expected)"
                        )
                    if isinstance(value, Buffer):
                        persistent = value.persistent
                    else:
                        persistent = name not in self._non_persistent_buffers_set
                    # === HACK ===
                    # This whole block below should just be:
                    # self.register_buffer(name, value, persistent)

                    # But to support subclasses of nn.Module that (wrongfully) implement a
                    # register_buffer() method that doesn't have the "persistent"
                    # argument. Only pass it in if it is accepted otherwise assume
                    # it is always true
                    if (
                        getattr(self.register_buffer, "__func__", None)
                        is torch.nn.Module.register_buffer
                    ):
                        self.register_buffer(name, value, persistent)
                    else:
                        sign = inspect.signature(self.register_buffer)
                        if "persistent" in sign.parameters:
                            self.register_buffer(name, value, persistent)
                        else:
                            if not persistent:
                                raise RuntimeError(
                                    "Registering a non-persistent buffer "
                                    "on a Module subclass that implements "
                                    "register_buffer() without the persistent "
                                    "argument is not allowed."
                                )
                            # Assume that the implementation without the argument has the
                            # behavior from before the argument was added: persistent=True
                            self.register_buffer(name, value)
                    # === HACK END ===
                else:
                    super().__setattr__(name, value)