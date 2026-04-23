def _set_default_effect(self) -> None:
        self._effect: EffectType | None = None

        # If the op contains a ScriptObject input, we want to mark it as having effects
        namespace, opname = torch._library.utils.parse_namespace(self.qualname)
        split = opname.split(".")
        if len(split) > 1:
            if len(split) != 2:
                raise AssertionError(
                    f"Tried to split {opname} based on '.' but found more than 1 '.'"
                )
            opname, overload = split
        else:
            overload = ""

        if namespace == "higher_order":
            return

        opname = f"{namespace}::{opname}"
        if torch._C._get_operation_overload(opname, overload) is not None:
            # Since we call this when destroying the library, sometimes the
            # schema will be gone already at that time.
            schema = torch._C._get_schema(opname, overload)
            for arg in schema.arguments:
                if isinstance(arg.type, torch.ClassType):
                    type_str = arg.type.str()  # pyrefly: ignore[missing-attribute]
                    if type_str in skip_classes:
                        continue
                    self._effect = EffectType.ORDERED
                    return