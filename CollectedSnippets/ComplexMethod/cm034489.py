def get_password_value(module, pkg, question, vtype):
    getsel = module.get_bin_path('debconf-get-selections', True)
    cmd = [getsel]
    rc, out, err = module.run_command(cmd)
    if rc != 0:
        module.fail_json(msg=f"Failed to get the value '{question}' from '{pkg}': {err}")

    for line in out.split("\n"):
        if not line.startswith(pkg):
            continue

        # line is a collection of tab separated values
        fields = line.split('\t')
        if len(fields) <= 3:
            # No password found, return a blank password
            return ''
        try:
            if fields[1] == question and fields[2] == vtype:
                # If correct question and question type found, return password value
                return fields[3]
        except IndexError:
            # Fail safe
            return ''