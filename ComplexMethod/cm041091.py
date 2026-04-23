def _compute_fn_select(args: list[Any]) -> Any:
            values = args[1]
            # defer evaluation if the selection list contains unresolved elements (e.g., unresolved intrinsics)
            if isinstance(values, list) and not all(isinstance(value, str) for value in values):
                raise RuntimeError("Fn::Select list contains unresolved elements")

            if not isinstance(values, list) or not values:
                raise ValidationError(
                    "Template error: Fn::Select requires a list argument with two elements: an integer index and a list"
                )
            try:
                index: int = int(args[0])
            except ValueError as e:
                raise ValidationError(
                    "Template error: Fn::Select requires a list argument with two elements: an integer index and a list"
                ) from e

            values_len = len(values)
            if index < 0 or index >= values_len:
                raise ValidationError(
                    "Template error: Fn::Select requires a list argument with two elements: an integer index and a list"
                )
            selection = values[index]
            return selection