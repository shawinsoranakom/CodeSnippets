def main():
    module = AnsibleModule(
        argument_spec=dict(
            path=dict(type='path', required=True, aliases=['dest', 'destfile', 'name']),
            state=dict(type='str', default='present', choices=['absent', 'present']),
            marker=dict(type='str', default='# {mark} ANSIBLE MANAGED BLOCK'),
            block=dict(type='str', default='', aliases=['content']),
            insertafter=dict(type='str'),
            insertbefore=dict(type='str'),
            create=dict(type='bool', default=False),
            backup=dict(type='bool', default=False),
            validate=dict(type='str'),
            marker_begin=dict(type='str', default='BEGIN'),
            marker_end=dict(type='str', default='END'),
            append_newline=dict(type='bool', default=False),
            prepend_newline=dict(type='bool', default=False),
            encoding=dict(type='str', default='utf-8'),
        ),
        mutually_exclusive=[['insertbefore', 'insertafter']],
        add_file_common_args=True,
        supports_check_mode=True
    )
    params = module.params
    path = params['path']

    encoding = module.params.get('encoding', None)

    if os.path.isdir(path):
        module.fail_json(rc=256,
                         msg='Path %s is a directory !' % path)

    path_exists = os.path.exists(path)
    if not path_exists:
        if not module.boolean(params['create']):
            module.fail_json(rc=257,
                             msg='Path %s does not exist !' % path)
        destpath = os.path.dirname(path)
        if destpath and not os.path.exists(destpath) and not module.check_mode:
            try:
                os.makedirs(destpath)
            except OSError as e:
                module.fail_json(msg='Error creating %s Error code: %s Error description: %s' % (destpath, e.errno, e.strerror))
            except Exception as e:
                module.fail_json(msg='Error creating %s Error: %s' % (destpath, to_native(e)))
        original = None
        lines = []
    else:
        # newline param set to preserve newline sequences read from file
        with open(path, 'r', encoding=encoding, newline='') as f:
            original = f.read()
        lines = original.splitlines(True)

    diff = {'before': '',
            'after': '',
            'before_header': '%s (content)' % path,
            'after_header': '%s (content)' % path}

    if module._diff and original:
        diff['before'] = original

    insertbefore = params['insertbefore']
    insertafter = params['insertafter']
    block = params['block']
    marker = params['marker']
    present = params['state'] == 'present'

    line_separator = os.linesep
    blank_line = [line_separator]

    if not present and not path_exists:
        module.exit_json(changed=False, msg="File %s not present" % path)

    if insertbefore is None and insertafter is None:
        insertafter = 'EOF'

    if insertafter not in (None, 'EOF'):
        insertre = re.compile(insertafter)
    elif insertbefore not in (None, 'BOF'):
        insertre = re.compile(insertbefore)
    else:
        insertre = None

    marker0 = re.sub(r'{mark}', params['marker_begin'], marker) + line_separator
    marker1 = re.sub(r'{mark}', params['marker_end'], marker) + line_separator

    if present and block:
        if not block.endswith(line_separator):
            block += line_separator

        blocklines = [marker0] + block.splitlines(True) + [marker1]
    else:
        blocklines = []

    n0 = n1 = None
    for i, line in enumerate(lines):
        if line == marker0:
            n0 = i
        if line == marker1:
            n1 = i

    if None in (n0, n1):
        n0 = None
        if insertre is not None:
            if insertre.flags & re.MULTILINE:
                match = insertre.search(original)
                if match:
                    if insertafter:
                        n0 = original.count('\n', 0, match.end())
                    elif insertbefore:
                        n0 = original.count('\n', 0, match.start())
            else:
                for i, line in enumerate(lines):
                    if insertre.search(line):
                        n0 = i
            if n0 is None:
                n0 = len(lines)
            elif insertafter is not None:
                n0 += 1
        elif insertbefore is not None:
            n0 = 0  # insertbefore=BOF
        else:
            n0 = len(lines)  # insertafter=EOF
    elif n0 < n1:
        lines[n0:n1 + 1] = []
    else:
        lines[n1:n0 + 1] = []
        n0 = n1

    # Ensure there is a line separator before the block of lines to be inserted
    if n0 > 0:
        if not lines[n0 - 1].endswith(line_separator):
            lines[n0 - 1] += line_separator

    # Before the block: check if we need to prepend a blank line
    # If yes, we need to add the blank line if we are not at the beginning of the file
    # and the previous line is not a blank line
    # In both cases, we need to shift by one on the right the inserting position of the block
    if params['prepend_newline'] and present:
        if n0 != 0 and lines[n0 - 1] != line_separator:
            lines[n0:n0] = blank_line
            n0 += 1

    # Insert the block
    lines[n0:n0] = blocklines

    # After the block: check if we need to append a blank line
    # If yes, we need to add the blank line if we are not at the end of the file
    # and the line right after is not a blank line
    if params['append_newline'] and present:
        line_after_block = n0 + len(blocklines)
        if line_after_block < len(lines) and lines[line_after_block] != line_separator:
            lines[line_after_block:line_after_block] = blank_line

    if lines:
        result = ''.join(lines)
    else:
        result = ''

    if module._diff:
        diff['after'] = result

    if original == result:
        msg = ''
        changed = False
    elif original is None:
        msg = 'File created'
        changed = True
    elif not blocklines:
        msg = 'Block removed'
        changed = True
    else:
        msg = 'Block inserted'
        changed = True

    backup_file = None
    if changed and not module.check_mode:
        if module.boolean(params['backup']) and path_exists:
            backup_file = module.backup_local(path)
        # We should always follow symlinks so that we change the real file
        real_path = os.path.realpath(params['path'])
        write_changes(module, result, real_path, encoding)

    if module.check_mode and not path_exists:
        module.exit_json(changed=changed, msg=msg, diff=diff)

    attr_diff = {}
    msg, changed = check_file_attrs(module, changed, msg, attr_diff)

    attr_diff['before_header'] = '%s (file attributes)' % path
    attr_diff['after_header'] = '%s (file attributes)' % path

    difflist = [diff, attr_diff]

    if backup_file is None:
        module.exit_json(changed=changed, msg=msg, diff=difflist)
    else:
        module.exit_json(changed=changed, msg=msg, diff=difflist, backup_file=backup_file)