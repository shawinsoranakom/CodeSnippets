def absent(module, dest, regexp, search_string, line, backup):

    b_dest = to_bytes(dest, errors='surrogate_or_strict')
    if not os.path.exists(b_dest):
        module.exit_json(changed=False, msg="file not present")

    msg = ''
    diff = {'before': '',
            'after': '',
            'before_header': '%s (content)' % dest,
            'after_header': '%s (content)' % dest}

    encoding = module.params['encoding']

    with open(b_dest, 'r', encoding=encoding) as f:
        lines = f.readlines()

    if module._diff:
        diff['before'] = ''.join(lines)

    if regexp is not None:
        re_c = re.compile(regexp)
    found = []

    def matcher(cur_line):
        if regexp is not None:
            match_found = re_c.search(cur_line)
        elif search_string is not None:
            match_found = search_string in cur_line
        else:
            match_found = line == cur_line.rstrip('\r\n')
        if match_found:
            found.append(cur_line)
        return not match_found

    lines = [l for l in lines if matcher(l)]
    changed = len(found) > 0

    if module._diff:
        diff['after'] = ''.join(lines)

    backupdest = ""
    if changed and not module.check_mode:
        if backup:
            backupdest = module.backup_local(dest)
        write_changes(module, lines, dest, encoding)

    if changed:
        msg = "%s line(s) removed" % len(found)

    attr_diff = {}
    msg, changed = check_file_attrs(module, changed, msg, attr_diff)

    attr_diff['before_header'] = '%s (file attributes)' % dest
    attr_diff['after_header'] = '%s (file attributes)' % dest

    difflist = [diff, attr_diff]

    module.exit_json(changed=changed, found=len(found), msg=msg, backup=backupdest, diff=difflist)