def parse_array(
        self,
        array: str,
        original_request_params: str,
    ) -> tuple[list[int | str], str]:
        """Parse the array from the request parameters.

        Args:
            array: The array string to parse.
            original_request_params: The original request parameters string.

        Returns:
            A tuple containing the parsed array and the stripped request parameters.

        Raises:
            OutputParserException: If the array format is invalid or cannot be parsed.
        """
        parsed_array: list[int | str] = []

        # Check if the format is [1,3,5]
        if re.match(r"\[\d+(,\s*\d+)*\]", array):
            parsed_array = [int(i) for i in re.findall(r"\d+", array)]
        # Check if the format is [1..5]
        elif re.match(r"\[(\d+)\.\.(\d+)\]", array):
            match = re.match(r"\[(\d+)\.\.(\d+)\]", array)
            if match:
                start, end = map(int, match.groups())
                parsed_array = list(range(start, end + 1))
            else:
                msg = f"Unable to parse the array provided in {array}. \
                        Please check the format instructions."
                raise OutputParserException(msg)
        # Check if the format is ["column_name"]
        elif re.match(r"\[[a-zA-Z0-9_]+(?:,[a-zA-Z0-9_]+)*\]", array):
            match = re.match(r"\[[a-zA-Z0-9_]+(?:,[a-zA-Z0-9_]+)*\]", array)
            if match:
                parsed_array = list(map(str, match.group().strip("[]").split(",")))
            else:
                msg = f"Unable to parse the array provided in {array}. \
                        Please check the format instructions."
                raise OutputParserException(msg)

        # Validate the array
        if not parsed_array:
            msg = f"Invalid array format in '{original_request_params}'. \
                    Please check the format instructions."
            raise OutputParserException(msg)
        if (
            isinstance(parsed_array[0], int)
            and parsed_array[-1] > self.dataframe.index.max()
        ):
            msg = f"The maximum index {parsed_array[-1]} exceeds the maximum index of \
                    the Pandas DataFrame {self.dataframe.index.max()}."
            raise OutputParserException(msg)

        return parsed_array, original_request_params.split("[", maxsplit=1)[0]