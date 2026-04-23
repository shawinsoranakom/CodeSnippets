def validate(self) -> None:
        type_hints = get_type_hints(self.__class__, include_extras=True)
        shape_env = dict[str, int]()

        for field_name, field_type in type_hints.items():
            # Check if field is missing
            if not hasattr(self, field_name) or getattr(self, field_name) is None:
                # Check if field is marked as optional
                actual_type = field_type
                if get_origin(field_type) is Annotated:
                    args = get_args(field_type)
                    actual_type = args[0]

                # Check arg was provided as Union
                if get_origin(actual_type) in {Union, UnionType}:
                    # Union for Union[X, Y] and UnionType for X | Y
                    args = get_args(actual_type)
                    # Skip validation when Union contains None
                    if type(None) in args:
                        continue
                # Otherwise field is required, raise error
                raise ValueError(f"Required field '{field_name}' is missing")

            # Field exists, proceed with validation
            value = getattr(self, field_name)
            if get_origin(field_type) is not None:
                args = get_args(field_type)

                for arg in args:
                    if isinstance(arg, TensorShape):
                        expected_shape = arg.resolve(**self._resolve_bindings)
                        actual_shape = self._validate_field(
                            value,
                            field_name,
                            expected_shape,
                            arg.dynamic_dims,
                        )

                        self._validate_tensor_shape_expected(
                            actual_shape,
                            expected_shape,
                            field_name,
                            shape_env,
                            arg.dynamic_dims,
                        )