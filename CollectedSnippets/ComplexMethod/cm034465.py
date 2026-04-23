def head_splitter(headfile, remote, module=None, fail_on_error=False):
    """Extract the head reference"""
    # https://github.com/ansible/ansible-modules-core/pull/907

    res = None
    if os.path.exists(headfile):
        rawdata = None
        try:
            with open(headfile, 'r') as f:
                rawdata = f.readline()
        except Exception:
            if fail_on_error and module:
                module.fail_json(msg="Unable to read %s" % headfile)
        if rawdata:
            try:
                rawdata = rawdata.replace('refs/remotes/%s' % remote, '', 1)
                refparts = rawdata.split(' ')
                newref = refparts[-1]
                nrefparts = newref.split('/', 2)
                res = nrefparts[-1].rstrip('\n')
            except Exception:
                if fail_on_error and module:
                    module.fail_json(msg="Unable to split head from '%s'" % rawdata)
    return res