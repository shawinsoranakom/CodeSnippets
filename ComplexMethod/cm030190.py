def filemode(mode):
    """Convert a file's mode to a string of the form '-rwxrwxrwx'."""
    perm = []
    for index, table in enumerate(_filemode_table):
        for bit, char in table:
            if index == 0:
                if S_IFMT(mode) == bit:
                    perm.append(char)
                    break
            else:
                if mode & bit == bit:
                    perm.append(char)
                    break
        else:
            if index == 0:
                # Unknown filetype
                perm.append("?")
            else:
                perm.append("-")
    return "".join(perm)