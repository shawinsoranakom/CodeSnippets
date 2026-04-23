def main():

    global module

    module = AnsibleModule(
        argument_spec=dict(
            state=dict(type='str', choices=['absent', 'directory', 'file', 'hard', 'link', 'touch']),
            path=dict(type='path', required=True, aliases=['dest', 'name']),
            _original_basename=dict(type='str'),  # Internal use only, for recursive ops
            recurse=dict(type='bool', default=False),
            force=dict(type='bool', default=False),  # Note: Should not be in file_common_args in future
            follow=dict(type='bool', default=True),  # Note: Different default than file_common_args
            _diff_peek=dict(type='bool'),  # Internal use only, for internal checks in the action plugins
            src=dict(type='path'),  # Note: Should not be in file_common_args in future
            modification_time=dict(type='str'),
            modification_time_format=dict(type='str', default='%Y%m%d%H%M.%S'),
            access_time=dict(type='str'),
            access_time_format=dict(type='str', default='%Y%m%d%H%M.%S'),
        ),
        add_file_common_args=True,
        supports_check_mode=True,
    )

    try:
        additional_parameter_handling(module.params)
        params = module.params

        state = params['state']
        recurse = params['recurse']
        force = params['force']
        follow = params['follow']
        path = params['path']
        src = params['src']

        if module.check_mode and state != 'absent':
            file_args = module.load_file_common_arguments(module.params)
            if file_args['owner']:
                check_owner_exists(module, file_args['owner'])
            if file_args['group']:
                check_group_exists(module, file_args['group'])

        timestamps = {}
        timestamps['modification_time'] = keep_backward_compatibility_on_timestamps(params['modification_time'], state)
        timestamps['modification_time_format'] = params['modification_time_format']
        timestamps['access_time'] = keep_backward_compatibility_on_timestamps(params['access_time'], state)
        timestamps['access_time_format'] = params['access_time_format']

        # short-circuit for diff_peek
        if params['_diff_peek'] is not None:
            appears_binary = execute_diff_peek(to_bytes(path, errors='surrogate_or_strict'))
            module.exit_json(path=path, changed=False, appears_binary=appears_binary)

        if state == 'file':
            result = ensure_file_attributes(path, follow, timestamps)
        elif state == 'directory':
            result = ensure_directory(path, follow, recurse, timestamps)
        elif state == 'link':
            result = ensure_symlink(path, src, follow, force, timestamps)
        elif state == 'hard':
            result = ensure_hardlink(path, src, follow, force, timestamps)
        elif state == 'touch':
            result = execute_touch(path, follow, timestamps)
        elif state == 'absent':
            result = ensure_absent(path)
    except AnsibleModuleError as ex:
        module.fail_json(**ex.results)

    if not module._diff:
        result.pop('diff', None)

    module.exit_json(**result)