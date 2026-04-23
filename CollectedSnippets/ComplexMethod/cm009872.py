def parse(self, request: str) -> dict[str, Any]:
        stripped_request_params = None
        splitted_request = request.strip().split(":")
        if len(splitted_request) != 2:  # noqa: PLR2004
            msg = f"Request '{request}' is not correctly formatted. \
                    Please refer to the format instructions."
            raise OutputParserException(msg)
        result = {}
        try:
            request_type, request_params = splitted_request
            if request_type in {"Invalid column", "Invalid operation"}:
                msg = f"{request}. Please check the format instructions."
                raise OutputParserException(msg)
            array_exists = re.search(r"(\[.*?\])", request_params)
            if array_exists:
                parsed_array, stripped_request_params = self.parse_array(
                    array_exists.group(1),
                    request_params,
                )
                if request_type == "column":
                    filtered_df = self.dataframe[
                        self.dataframe.index.isin(parsed_array)
                    ]
                    if len(parsed_array) == 1:
                        result[stripped_request_params] = filtered_df[
                            stripped_request_params
                        ].iloc[parsed_array[0]]
                    else:
                        result[stripped_request_params] = filtered_df[
                            stripped_request_params
                        ]
                elif request_type == "row":
                    filtered_df = self.dataframe[
                        self.dataframe.columns.intersection(parsed_array)
                    ]
                    if len(parsed_array) == 1:
                        result[stripped_request_params] = filtered_df.iloc[
                            int(stripped_request_params)
                        ][parsed_array[0]]
                    else:
                        result[stripped_request_params] = filtered_df.iloc[
                            int(stripped_request_params)
                        ]
                else:
                    filtered_df = self.dataframe[
                        self.dataframe.index.isin(parsed_array)
                    ]
                    result[request_type] = getattr(
                        filtered_df[stripped_request_params],
                        request_type,
                    )()
            elif request_type == "column":
                result[request_params] = self.dataframe[request_params]
            elif request_type == "row":
                result[request_params] = self.dataframe.iloc[int(request_params)]
            else:
                result[request_type] = getattr(
                    self.dataframe[request_params],
                    request_type,
                )()
        except (AttributeError, IndexError, KeyError) as e:
            if request_type not in {"column", "row"}:
                msg = f"Unsupported request type '{request_type}'. \
                        Please check the format instructions."
                raise OutputParserException(msg) from e
            msg = f"""Requested index {
                request_params
                if stripped_request_params is None
                else stripped_request_params
            } is out of bounds."""
            raise OutputParserException(msg) from e

        return result