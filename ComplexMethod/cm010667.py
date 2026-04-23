def __init__(self, orig, id_set=None, _compilation_unit=None):
        # XXX: orig can be a nn.Module or a function!
        super().__init__()
        if not isinstance(orig, torch.nn.Module):
            raise AssertionError(f"Expected nn.Module, got {type(orig)}")

        # Copy a subset of `orig` to a temporary nn.Module.
        # This is a way to customize what will actually get compiled by create_script_module
        id_set = set()

        # This allows us to preserve the original module's qualified name by defining a new
        # type with the attribute _jit_override_qualname. In torch._jit_internal._qualified_name
        # we have a special case that will look up this attribute to override whatever qualname
        # we would get from the python type system
        class QualnameWrapper(torch.nn.Module):
            pass

        QualnameWrapper._jit_override_qualname = torch._jit_internal._qualified_name(  # type: ignore[attr-defined]
            type(orig)
        )

        tmp_module = QualnameWrapper()

        def check_unique(param):
            if param in id_set:
                raise ValueError(
                    "TracedModules don't support parameter sharing between modules"
                )
            id_set.add(param)

        tmp_module.training = orig.training

        for name, param in orig._parameters.items():
            if param is not None:
                tmp_module._parameters[name] = param
                check_unique(param)
        for name, buf in orig._buffers.items():
            if buf is not None:
                tmp_module._buffers[name] = buf
                check_unique(buf)
        for name, val in orig.__dict__.items():
            if (
                torch._C._jit_is_script_object(val)
                and name not in orig._parameters
                and name not in orig._buffers
            ):
                setattr(tmp_module, name, val)

        if orig._backward_hooks:
            raise ValueError(
                "Modules that have backward hooks assigned can't be compiled: "
                + str(orig)
            )

        for name, submodule in orig._modules.items():
            if submodule is None:
                continue
            tmp_module._modules[name] = make_module(
                submodule, TracedModule, _compilation_unit=None
            )

        script_module = torch.jit._recursive.create_script_module(
            tmp_module, lambda module: (), share_types=False, is_tracing=True
        )

        self.__dict__["_name"] = type(orig).__name__
        self.__dict__["_actual_script_module"] = script_module
        for name in ("_parameters", "_buffers", "_modules", "training"):
            delattr(self, name)