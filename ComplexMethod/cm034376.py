def main():

    # the command module is the one ansible module that does not take key=value args
    # hence don't copy this one if you are looking to build others!
    # NOTE: ensure splitter.py is kept in sync for exceptions
    module = AnsibleModule(
        argument_spec=dict(
            _raw_params=dict(),
            _uses_shell=dict(type='bool', default=False),
            cmd=dict(),
            argv=dict(type='list', elements='str'),
            chdir=dict(type='path'),
            executable=dict(),
            expand_argument_vars=dict(type='bool', default=True),
            creates=dict(type='path'),
            removes=dict(type='path'),
            # The default for this really comes from the action plugin
            stdin=dict(required=False),
            stdin_add_newline=dict(type='bool', default=True),
            strip_empty_ends=dict(type='bool', default=True),
        ),
        required_one_of=[['_raw_params', 'cmd', 'argv']],
        mutually_exclusive=[['_raw_params', 'cmd', 'argv']],
        supports_check_mode=True,
    )
    shell = module.params['_uses_shell']
    chdir = module.params['chdir']
    executable = module.params['executable']
    args = module.params['_raw_params'] or module.params['cmd']
    argv = module.params['argv']
    creates = module.params['creates']
    removes = module.params['removes']
    stdin = module.params['stdin']
    stdin_add_newline = module.params['stdin_add_newline']
    strip = module.params['strip_empty_ends']
    expand_argument_vars = module.params['expand_argument_vars']

    # we promised these in 'always' ( _lines get auto-added on action plugin)
    r = {'changed': False, 'stdout': '', 'stderr': '', 'rc': None, 'cmd': None, 'start': None, 'end': None, 'delta': None, 'msg': ''}

    if not shell and executable:
        module.warn("As of Ansible 2.4, the parameter 'executable' is no longer supported with the 'command' module. Not using '%s'." % executable)
        executable = None

    if not shell and args:
        args = shlex.split(args)

    args = args or argv
    # All args must be strings
    if is_iterable(args, include_strings=False):
        args = [to_native(arg, errors='surrogate_or_strict', nonstring='simplerepr') for arg in args]

    r['cmd'] = args

    if chdir:
        chdir = to_bytes(chdir, errors='surrogate_or_strict')

        try:
            os.chdir(chdir)
        except OSError as ex:
            r['msg'] = 'Unable to change directory before execution.'
            module.fail_json(**r, exception=ex)

    # check_mode partial support, since it only really works in checking creates/removes
    if module.check_mode:
        shoulda = "Would"
    else:
        shoulda = "Did"

    # special skips for idempotence if file exists (assumes command creates)
    if creates:
        if glob.glob(creates):
            r['msg'] = "%s not run command since '%s' exists" % (shoulda, creates)
            r['stdout'] = "skipped, since %s exists" % creates  # TODO: deprecate

            r['rc'] = 0

    # special skips for idempotence if file does not exist (assumes command removes)
    if not r['msg'] and removes:
        if not glob.glob(removes):
            r['msg'] = "%s not run command since '%s' does not exist" % (shoulda, removes)
            r['stdout'] = "skipped, since %s does not exist" % removes  # TODO: deprecate
            r['rc'] = 0

    if r['msg']:
        module.exit_json(**r)

    r['changed'] = True

    # actually executes command (or not ...)
    if not module.check_mode:
        r['start'] = datetime.datetime.now()
        r['rc'], r['stdout'], r['stderr'] = module.run_command(args, executable=executable, use_unsafe_shell=shell, encoding=None,
                                                               data=stdin, binary_data=(not stdin_add_newline),
                                                               expand_user_and_vars=expand_argument_vars)
        r['end'] = datetime.datetime.now()
    else:
        # this is partial check_mode support, since we end up skipping if we get here
        r['rc'] = 0
        r['msg'] = "Command would have run if not in check mode"
        if creates is None and removes is None:
            r['skipped'] = True
            # skipped=True and changed=True are mutually exclusive
            r['changed'] = False

    # convert to text for jsonization and usability
    if r['start'] is not None and r['end'] is not None:
        # these are datetime objects, but need them as strings to pass back
        r['delta'] = to_text(r['end'] - r['start'])
        r['end'] = to_text(r['end'])
        r['start'] = to_text(r['start'])

    if strip:
        r['stdout'] = to_text(r['stdout']).rstrip("\r\n")
        r['stderr'] = to_text(r['stderr']).rstrip("\r\n")

    if r['rc'] != 0:
        r['msg'] = 'The command exited with a non-zero return code.'
        module.fail_json(**r)

    module.exit_json(**r)