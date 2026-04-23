def check_json_file_has_correct_format(file_path):
    with open(file_path) as f:
        lines = f.readlines()
        if len(lines) == 1:
            # length can only be 1 if dict is empty
            assert lines[0] == "{}"
        else:
            # otherwise make sure json has correct format (at least 3 lines)
            assert len(lines) >= 3
            # each key one line, ident should be 2, min length is 3
            assert lines[0].strip() == "{"
            for line in lines[1:-1]:
                left_indent = len(lines[1]) - len(lines[1].lstrip())
                assert left_indent == 2
            assert lines[-1].strip() == "}"