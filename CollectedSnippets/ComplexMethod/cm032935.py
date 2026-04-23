def filter_out(v2docs, operator, value):
        ids = []
        for input, docids in v2docs.items():

            if operator in ["=", "≠", ">", "<", "≥", "≤"]:
                # Check if input is in YYYY-MM-DD date format
                input_str = str(input).strip()
                value_str = str(value).strip()

                # Strict date format detection: YYYY-MM-DD (must be 10 chars with correct format)
                is_input_date = (
                    len(input_str) == 10 and
                    input_str[4] == '-' and
                    input_str[7] == '-' and
                    input_str[:4].isdigit() and
                    input_str[5:7].isdigit() and
                    input_str[8:10].isdigit()
                )

                is_value_date = (
                    len(value_str) == 10 and
                    value_str[4] == '-' and
                    value_str[7] == '-' and
                    value_str[:4].isdigit() and
                    value_str[5:7].isdigit() and
                    value_str[8:10].isdigit()
                )

                if is_value_date:
                    # Query value is in date format
                    if is_input_date:
                        # Data is also in date format: perform date comparison
                        input = input_str
                        value = value_str
                    else:
                        # Data is not in date format: skip this record (no match)
                        continue
                else:
                    # Query value is not in date format: use original logic
                    try:
                        if isinstance(input, list):
                            input = input[0]
                        input = ast.literal_eval(input)
                        value = ast.literal_eval(value)
                    except Exception:
                        pass

                    # Convert strings to lowercase
                    if isinstance(input, str):
                        input = input.lower()
                    if isinstance(value, str):
                        value = value.lower()
            else:
                # Non-comparison operators: maintain original logic
                if isinstance(input, str):
                    input = input.lower()
                if isinstance(value, str):
                    value = value.lower()

            matched = False
            try:
                if operator == "contains":
                    matched = str(input).find(value) >= 0 if not isinstance(input, list) else any(str(i).find(value) >= 0 for i in input)
                elif operator == "not contains":
                    matched = str(input).find(value) == -1 if not isinstance(input, list) else all(str(i).find(value) == -1 for i in input)
                elif operator == "in":
                    matched = input in value if not isinstance(input, list) else all(i in value for i in input)
                elif operator == "not in":
                    matched = input not in value if not isinstance(input, list) else all(i not in value for i in input)
                elif operator == "start with":
                    matched = str(input).lower().startswith(str(value).lower()) if not isinstance(input, list) else "".join([str(i).lower() for i in input]).startswith(str(value).lower())
                elif operator == "end with":
                    matched = str(input).lower().endswith(str(value).lower()) if not isinstance(input, list) else "".join([str(i).lower() for i in input]).endswith(str(value).lower())
                elif operator == "empty":
                    matched = not input
                elif operator == "not empty":
                    matched = bool(input)
                elif operator == "=":
                    matched = input == value
                elif operator == "≠":
                    matched = input != value
                elif operator == ">":
                    matched = input > value
                elif operator == "<":
                    matched = input < value
                elif operator == "≥":
                    matched = input >= value
                elif operator == "≤":
                    matched = input <= value
            except Exception:
                pass

            if matched:
                ids.extend(docids)
        return ids