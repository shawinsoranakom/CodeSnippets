def repair_invalid_json(output: str, error: str) -> str:
    """
    repair the situation like there are extra chars like
    error examples
        example 1. json.decoder.JSONDecodeError: Expecting ',' delimiter: line 154 column 1 (char 2765)
        example 2. xxx.JSONDecodeError: Expecting property name enclosed in double quotes: line 14 column 1 (char 266)
    """
    pattern = r"line ([0-9]+) column ([0-9]+)"

    matches = re.findall(pattern, error, re.DOTALL)
    if len(matches) > 0:
        line_no = int(matches[0][0]) - 1
        col_no = int(matches[0][1]) - 1

        # due to CustomDecoder can handle `"": ''` or `'': ""`, so convert `"""` -> `"`, `'''` -> `'`
        output = output.replace('"""', '"').replace("'''", '"')
        arr = output.split("\n")
        rline = arr[line_no]  # raw line
        line = arr[line_no].strip()
        # different general problems
        if line.endswith("],"):
            # problem, redundant char `]`
            new_line = line.replace("]", "")
        elif line.endswith("},") and not output.endswith("},"):
            # problem, redundant char `}`
            new_line = line.replace("}", "")
        elif line.endswith("},") and output.endswith("},"):
            new_line = line[:-1]
        elif (rline[col_no] in ["'", '"']) and (line.startswith('"') or line.startswith("'")) and "," not in line:
            # problem, `"""` or `'''` without `,`
            new_line = f",{line}"
        elif col_no - 1 >= 0 and rline[col_no - 1] in ['"', "'"]:
            # backslash problem like \" in the output
            char = rline[col_no - 1]
            nearest_char_idx = rline[col_no:].find(char)
            new_line = (
                rline[: col_no - 1]
                + "\\"
                + rline[col_no - 1 : col_no + nearest_char_idx]
                + "\\"
                + rline[col_no + nearest_char_idx :]
            )
        elif '",' not in line and "," not in line and '"' not in line:
            new_line = f'{line}",'
        elif not line.endswith(","):
            # problem, miss char `,` at the end.
            new_line = f"{line},"
        elif "," in line and len(line) == 1:
            new_line = f'"{line}'
        elif '",' in line:
            new_line = line[:-2] + "',"
        else:
            new_line = line

        arr[line_no] = new_line
        output = "\n".join(arr)
        logger.info(f"repair_invalid_json, raw error: {error}")

    return output