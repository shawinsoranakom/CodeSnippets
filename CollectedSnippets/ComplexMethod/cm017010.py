def get_new_command(command):
    """
    Attempt to rebuild the path string by spellchecking the directories.
    If it fails (i.e. no directories are a close enough match), then it
    defaults to the rules of cd_mkdir.
    Change sensitivity by changing MAX_ALLOWED_DIFF. Default value is 0.6
    """
    dest = command.script_parts[1].split(os.sep)
    if dest[-1] == '':
        dest = dest[:-1]

    if dest[0] == '':
        cwd = os.sep
        dest = dest[1:]
    elif six.PY2:
        cwd = os.getcwdu()
    else:
        cwd = os.getcwd()
    for directory in dest:
        if directory == ".":
            continue
        elif directory == "..":
            cwd = os.path.split(cwd)[0]
            continue
        best_matches = get_close_matches(directory, _get_sub_dirs(cwd), cutoff=MAX_ALLOWED_DIFF)
        if best_matches:
            cwd = os.path.join(cwd, best_matches[0])
        else:
            return cd_mkdir.get_new_command(command)
    return u'cd "{0}"'.format(cwd)