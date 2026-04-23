def main():
    module = AnsibleModule(
        argument_spec=dict(
            path=dict(type='path', required=True, aliases=['dest', 'destfile', 'name']),
            regexp=dict(type='str', required=True),
            replace=dict(type='str', default=''),
            after=dict(type='str'),
            before=dict(type='str'),
            backup=dict(type='bool', default=False),
            validate=dict(type='str'),
            encoding=dict(type='str', default='utf-8'),
        ),
        add_file_common_args=True,
        supports_check_mode=True,
    )

    params = module.params
    path = params['path']
    encoding = params['encoding']
    res_args = dict(rc=0)
    contents = None

    params['after'] = to_text(params['after'], errors='surrogate_or_strict', nonstring='passthru')
    params['before'] = to_text(params['before'], errors='surrogate_or_strict', nonstring='passthru')
    params['regexp'] = to_text(params['regexp'], errors='surrogate_or_strict', nonstring='passthru')
    params['replace'] = to_text(params['replace'], errors='surrogate_or_strict', nonstring='passthru')

    if os.path.isdir(path):
        module.fail_json(rc=256, msg='Path %s is a directory !' % path)

    if not os.path.exists(path):
        module.fail_json(rc=257, msg='Path %s does not exist !' % path)
    else:
        try:
            with open(path, 'r', encoding=encoding) as f:
                contents = f.read()
        except OSError as ex:
            raise Exception(f"Unable to read the contents of {path!r}.") from ex

    pattern = u''
    if params['after'] and params['before']:
        pattern = u'%s(?P<subsection>.*?)%s' % (params['after'], params['before'])
    elif params['after']:
        pattern = u'%s(?P<subsection>.*)' % params['after']
    elif params['before']:
        pattern = u'(?P<subsection>.*)%s' % params['before']

    if pattern:
        section_re = re.compile(pattern, re.DOTALL)
        match = re.search(section_re, contents)
        if match:
            section = match.group('subsection')
            indices = [match.start('subsection'), match.end('subsection')]
        else:
            res_args['msg'] = 'Pattern for before/after params did not match the given file: %s' % pattern
            res_args['changed'] = False
            module.exit_json(**res_args)
    else:
        section = contents

    mre = re.compile(params['regexp'], re.MULTILINE)
    try:
        result = re.subn(mre, params['replace'], section, 0)
    except re.error as e:
        module.fail_json(msg="Unable to process replace due to error: %s" % to_text(e))

    if result[1] > 0 and section != result[0]:
        if pattern:
            result = (contents[:indices[0]] + result[0] + contents[indices[1]:], result[1])
        msg = '%s replacements made' % result[1]
        changed = True
        if module._diff:
            res_args['diff'] = {
                'before_header': path,
                'before': contents,
                'after_header': path,
                'after': result[0],
            }
    else:
        msg = ''
        changed = False

    if changed and not module.check_mode:
        if params['backup'] and os.path.exists(path):
            res_args['backup_file'] = module.backup_local(path)
        # We should always follow symlinks so that we change the real file
        path = os.path.realpath(path)
        write_changes(module, result[0], path, encoding=encoding)

    res_args['msg'], res_args['changed'] = check_file_attrs(module, changed, msg)
    module.exit_json(**res_args)