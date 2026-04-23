async def run(self, input_data: Input, **kwargs) -> BlockOutput:

        # If input_data.value is not matching input_data.input, convert value to type of input
        if (
            input_data.input != input_data.value
            and input_data.input is not input_data.value
        ):
            try:
                # Only attempt conversion if input is not None and value is not None
                if input_data.input is not None and input_data.value is not None:
                    input_type = type(input_data.input)
                    # Avoid converting if input_type is Any or object
                    if input_type not in (Any, object):
                        input_data.value = convert(input_data.value, input_type)
            except Exception:
                pass  # If conversion fails, just leave value as is

        if input_data.input == input_data.value:
            yield "result", True
            yield "yes_output", input_data.yes_value
        else:
            yield "result", False
            yield "no_output", input_data.no_value