def repair_json_format(output: str) -> str:
    """
    fix extra `[` or `}` in the end
    """
    output = output.strip()

    if output.startswith("[{"):
        output = output[1:]
        logger.info(f"repair_json_format: {'[{'}")
    elif output.endswith("}]"):
        output = output[:-1]
        logger.info(f"repair_json_format: {'}]'}")
    elif output.startswith("{") and output.endswith("]"):
        output = output[:-1] + "}"

    # remove comments in output json string, after json value content, maybe start with #, maybe start with //
    arr = output.split("\n")
    new_arr = []
    for json_line in arr:
        # look for # or // comments and make sure they are not inside the string value
        comment_index = -1
        for match in re.finditer(r"(\".*?\"|\'.*?\')|(#|//)", json_line):
            if match.group(1):  # if the string value
                continue
            if match.group(2):  # if comments
                comment_index = match.start(2)
                break
        # if comments, then delete them
        if comment_index != -1:
            json_line = json_line[:comment_index].rstrip()
        new_arr.append(json_line)
    output = "\n".join(new_arr)
    return output