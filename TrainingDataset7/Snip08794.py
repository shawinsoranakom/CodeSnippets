def write_pot_file(potfile, msgs):
    """
    Write the `potfile` with the `msgs` contents, making sure its format is
    valid.
    """
    pot_lines = msgs.splitlines()
    if os.path.exists(potfile):
        # Strip the header
        lines = dropwhile(len, pot_lines)
    else:
        lines = []
        found, header_read = False, False
        for line in pot_lines:
            if not found and not header_read:
                if "charset=CHARSET" in line:
                    found = True
                    line = line.replace("charset=CHARSET", "charset=UTF-8")
            if not line and not found:
                header_read = True
            lines.append(line)
    msgs = "\n".join(lines)
    # Force newlines of POT files to '\n' to work around
    # https://savannah.gnu.org/bugs/index.php?52395
    with open(potfile, "a", encoding="utf-8", newline="\n") as fp:
        fp.write(msgs)