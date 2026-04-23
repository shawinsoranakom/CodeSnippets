def resources_list(string):
    u = []
    for x in string.split(','):
        r, eq, v = x.partition('=')
        r = r.lower()
        u.append((r, v if eq else None))
        if r == 'all' or r == 'none':
            if eq:
                raise argparse.ArgumentTypeError('invalid resource: ' + x)
            continue
        if r[0] == '-':
            if eq:
                raise argparse.ArgumentTypeError('invalid resource: ' + x)
            r = r[1:]
        if r not in RESOURCE_NAMES:
            raise argparse.ArgumentTypeError('invalid resource: ' + r)
    return u