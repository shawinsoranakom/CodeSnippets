def map_arg(arg: Any) -> Any:
            if isinstance(arg, VariableTracker) and arg.is_python_constant():
                return arg.as_python_constant()
            elif isinstance(arg, ListVariable) and not arg.items:
                # pyrefly: ignore [implicit-any]
                return []
            elif (
                isinstance(arg, ConstDictVariable)
                and isinstance(arg.source, GetItemSource)
                and isinstance(arg.source.base, AttrSource)
                and arg.source.base.member == "param_groups"
            ):
                return self.value.param_groups[arg.source.index]

            raise ArgMappingException