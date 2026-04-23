def get_output(self, result, input_key, output_key):
        """Retrieves the output value from the given result dictionary based on the specified input and output keys.

        Args:
            result (dict): The result dictionary containing the output value.
            input_key (str): The key used to retrieve the input value from the result dictionary.
            output_key (str): The key used to retrieve the output value from the result dictionary.

        Returns:
            tuple: A tuple containing the output value and the status message.

        """
        possible_output_keys = ["answer", "response", "output", "result", "text"]
        status = ""
        result_value = None

        if output_key in result:
            result_value = result.get(output_key)
        elif len(result) == 2 and input_key in result:  # noqa: PLR2004
            # get the other key from the result dict
            other_key = next(k for k in result if k != input_key)
            if other_key == output_key:
                result_value = result.get(output_key)
            else:
                status += f"Warning: The output key is not '{output_key}'. The output key is '{other_key}'."
                result_value = result.get(other_key)
        elif len(result) == 1:
            result_value = next(iter(result.values()))
        elif any(k in result for k in possible_output_keys):
            for key in possible_output_keys:
                if key in result:
                    result_value = result.get(key)
                    status += f"Output key: '{key}'."
                    break
            if result_value is None:
                result_value = result
                status += f"Warning: The output key is not '{output_key}'."
        else:
            result_value = result
            status += f"Warning: The output key is not '{output_key}'."

        return result_value, status