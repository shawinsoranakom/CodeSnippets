def check_details_tag(file_list):
    """
    Check whether the structure:
    <details>
    ...
    </details>

    Is correctly followed, if not generates an error.

    """

    after_detail = False
    error = False
    err_message = ""
    for line_number, line in enumerate(file_list):
        if b"<details>" in line and b"</details>" in line:
            pass
        else:
            if b"<details>" in line and after_detail:
                err_message = f"Missing closing detail tag round line {line_number - 1}"
                error = True
            if b"</details>" in line and not after_detail:
                err_message = f"Missing opening detail tag round line {line_number - 1}"
                error = True

            if b"<details>" in line:
                after_detail = True

            if b"</details>" in line and after_detail:
                after_detail = False

            if error:
                errors.append(err_message)

        error = False