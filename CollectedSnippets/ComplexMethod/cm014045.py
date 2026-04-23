def get_variable_cls(self, user_cls: type) -> type:
        from torch.overrides import TorchFunctionMode

        from .variables.ctx_manager import GenericContextWrappingVariable
        from .variables.torch_function import TorchFunctionModeVariable
        from .variables.user_defined import is_forbidden_context_manager

        variable_cls: type[variables.UserDefinedObjectVariable] = (
            variables.UserDefinedObjectVariable
        )
        if issubclass(
            user_cls, TorchFunctionMode
        ) and TorchFunctionModeVariable.is_supported_torch_function_mode(user_cls):
            variable_cls = TorchFunctionModeVariable
        elif (
            hasattr(user_cls, "__enter__")
            and hasattr(user_cls, "__exit__")
            and not is_forbidden_context_manager(user_cls)
        ):
            variable_cls = GenericContextWrappingVariable
        elif issubclass(user_cls, torch.nn.Module):
            variable_cls = variables.UnspecializedNNModuleVariable
        elif issubclass(user_cls, collections.defaultdict):
            variable_cls = variables.DefaultDictVariable
        elif issubclass(user_cls, collections.OrderedDict):
            variable_cls = variables.OrderedDictVariable
        elif issubclass(user_cls, dict):
            variable_cls = variables.UserDefinedDictVariable
        elif issubclass(user_cls, (set, frozenset)):
            variable_cls = variables.UserDefinedSetVariable
        elif issubclass(user_cls, tuple):
            if is_namedtuple_cls(user_cls):
                variable_cls = variables.UserDefinedTupleVariable.get_vt_cls(user_cls)
            else:
                variable_cls = variables.UserDefinedTupleVariable
        elif issubclass(user_cls, list):
            variable_cls = variables.UserDefinedListVariable
        elif issubclass(user_cls, MutableMapping):
            variable_cls = variables.MutableMappingVariable
        elif is_frozen_dataclass(user_cls):
            variable_cls = FrozenDataClassVariable
        elif issubclass(user_cls, BaseException):
            variable_cls = variables.UserDefinedExceptionObjectVariable
        elif issubclass(
            user_cls,
            variables.user_defined._CONSTANT_BASE_TYPES,
        ):
            variable_cls = variables.UserDefinedConstantVariable
        elif variables.InspectVariable.is_matching_class(user_cls):
            variable_cls = variables.InspectVariable
        assert issubclass(variable_cls, variables.UserDefinedObjectVariable)
        return variable_cls