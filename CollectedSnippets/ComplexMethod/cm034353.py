def parse_systemctl_show(lines):
    # The output of 'systemctl show' can contain values that span multiple lines. At first glance it
    # appears that such values are always surrounded by {}, so the previous version of this code
    # assumed that any value starting with { was a multi-line value; it would then consume lines
    # until it saw a line that ended with }. However, it is possible to have a single-line value
    # that starts with { but does not end with } (this could happen in the value for Description=,
    # for example), and the previous version of this code would then consume all remaining lines as
    # part of that value. Cryptically, this would lead to Ansible reporting that the service file
    # couldn't be found.
    #
    # To avoid this issue, the following code only accepts multi-line values for keys whose names
    # start with Exec (e.g., ExecStart=), since these are the only keys whose values are known to
    # span multiple lines.
    parsed = {}
    multival = []
    k = None
    for line in lines:
        if k is None:
            if '=' in line:
                k, v = line.split('=', 1)
                if k.startswith('Exec') and v.lstrip().startswith('{'):
                    if not v.rstrip().endswith('}'):
                        multival.append(v)
                        continue
                parsed[k] = v.strip()
                k = None
        else:
            multival.append(line)
            if line.rstrip().endswith('}'):
                parsed[k] = '\n'.join(multival).strip()
                multival = []
                k = None
    return parsed