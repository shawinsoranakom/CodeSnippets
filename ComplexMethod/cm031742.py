def getsetupinfo(filename):
    modules = {}
    variables = {}
    fp = open(filename)
    pendingline = ""
    try:
        while 1:
            line = fp.readline()
            if pendingline:
                line = pendingline + line
                pendingline = ""
            if not line:
                break
            # Strip comments
            i = line.find('#')
            if i >= 0:
                line = line[:i]
            if line.endswith('\\\n'):
                pendingline = line[:-2]
                continue
            matchobj = setupvardef.match(line)
            if matchobj:
                (name, value) = matchobj.group(1, 2)
                variables[name] = value.strip()
            else:
                words = line.split()
                if words:
                    modules[words[0]] = words[1:]
    finally:
        fp.close()
    return modules, variables