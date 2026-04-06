def match(command):
    if '-d' in command.script:
        return False

    zip_file = _zip_file(command)
    if zip_file:
        return _is_bad_zip(zip_file)
    else:
        return False