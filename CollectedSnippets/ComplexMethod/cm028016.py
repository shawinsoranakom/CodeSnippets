def check_summary_tag(file_list):
    """
    Check whether the structure:
    <summary>
    ...
    </summary>

    Is correctly followed, if not generates an error.

    """

    after_summary = False
    error = False
    err_message = ""
    for idx, line in enumerate(file_list):
        line_number = idx + 1
        if b"<summary>" in line and b"</summary>" in line:
            if after_summary:
                err_message = f"Missing closing summary tag around line {line_number}"
                error = True

        else:
            if b"<summary>" in line and after_summary:
                err_message = f"Missing closing summary tag around line {line_number}"
                error = True
            if b"</summary>" in line and not after_summary:
                err_message = f"Missing opening summary tag around line {line_number}"
                error = True

            if b"<summary>" in line:
                after_summary = True

            if b"</summary>" in line and after_summary:
                after_summary = False

        if error:
            errors.append(err_message)

        error = False