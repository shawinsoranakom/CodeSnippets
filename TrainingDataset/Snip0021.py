def main(filename: str) -> None:

    with open(filename, mode='r', encoding='utf-8') as file:
        lines = list(line.rstrip() for line in file)

    file_format_err_msgs = check_file_format(lines)

    if file_format_err_msgs:
        for err_msg in file_format_err_msgs:
            print(err_msg)
        sys.exit(1)
