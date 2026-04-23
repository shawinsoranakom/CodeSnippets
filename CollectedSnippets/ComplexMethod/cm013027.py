def from_value(
        cls, value: torch._C.Value | torch.Tensor | None, default=None
    ) -> JitScalarType:
        """Create a JitScalarType from an value's scalar type.

        Args:
            value: An object to fetch scalar type from.
            default: The JitScalarType to return if a valid scalar cannot be fetched from value

        Returns:
            JitScalarType.

        Raises:
            OnnxExporterError: if value does not have a valid scalar type and default is None.
            SymbolicValueError: when value.type()'s info are empty and default is None
        """

        if not isinstance(value, (torch._C.Value, torch.Tensor)) or (
            isinstance(value, torch._C.Value) and value.node().mustBeNone()
        ):
            # default value of type JitScalarType is returned when value is not valid
            if default is None:
                raise errors.OnnxExporterError(
                    "value must be either torch._C.Value or torch.Tensor objects."
                )
            elif not isinstance(default, JitScalarType):
                raise errors.OnnxExporterError(
                    "default value must be a JitScalarType object."
                )
            return default

        # Each value type has their own way of storing scalar type
        if isinstance(value, torch.Tensor):
            return cls.from_dtype(value.dtype)
        if isinstance(value.type(), torch.ListType):
            try:
                return cls.from_dtype(value.type().getElementType().dtype())
            except RuntimeError:
                return cls._from_name(str(value.type().getElementType()))
        if isinstance(value.type(), torch._C.OptionalType):
            if value.type().getElementType().dtype() is None:
                if isinstance(default, JitScalarType):
                    return default
                raise errors.OnnxExporterError(
                    "default value must be a JitScalarType object."
                )
            return cls.from_dtype(value.type().getElementType().dtype())

        scalar_type = None
        if value.node().kind() != "prim::Constant" or not isinstance(
            value.type(), torch._C.NoneType
        ):
            # value must be a non-list torch._C.Value scalar
            scalar_type = value.type().scalarType()

        if scalar_type is not None:
            return cls._from_name(scalar_type)

        # When everything fails... try to default
        if default is not None:
            return default
        raise errors.SymbolicValueError(
            f"Cannot determine scalar type for this '{type(value.type())}' instance and "
            "a default value was not provided.",
            value,
        )