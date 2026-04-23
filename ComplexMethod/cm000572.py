async def run(self, input_data: Input, **kwargs) -> BlockOutput:
        operator = input_data.operator

        value1 = input_data.value1
        if isinstance(value1, str):
            try:
                value1 = float(value1.strip())
            except ValueError:
                value1 = value1.strip()

        value2 = input_data.value2
        if isinstance(value2, str):
            try:
                value2 = float(value2.strip())
            except ValueError:
                value2 = value2.strip()

        yes_value = input_data.yes_value if input_data.yes_value is not None else value1
        no_value = input_data.no_value if input_data.no_value is not None else value2

        comparison_funcs = {
            ComparisonOperator.EQUAL: lambda a, b: a == b,
            ComparisonOperator.NOT_EQUAL: lambda a, b: a != b,
            ComparisonOperator.GREATER_THAN: lambda a, b: a > b,
            ComparisonOperator.LESS_THAN: lambda a, b: a < b,
            ComparisonOperator.GREATER_THAN_OR_EQUAL: lambda a, b: a >= b,
            ComparisonOperator.LESS_THAN_OR_EQUAL: lambda a, b: a <= b,
        }

        try:
            result = comparison_funcs[operator](value1, value2)
        except Exception as e:
            raise ValueError(f"Comparison failed: {e}") from e

        yield "result", result

        if result:
            yield "yes_output", yes_value
        else:
            yield "no_output", no_value