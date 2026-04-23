def start_connection(play_context, options, task_uuid):
    """
    Starts the persistent connection
    """

    env = os.environ.copy()
    env.update({
        # HACK; most of these paths may change during the controller's lifetime
        # (eg, due to late dynamic role includes, multi-playbook execution), without a way
        # to invalidate/update, the persistent connection helper won't always see the same plugins the controller
        # can.
        'ANSIBLE_BECOME_PLUGINS': become_loader.print_paths(),
        'ANSIBLE_CLICONF_PLUGINS': cliconf_loader.print_paths(),
        'ANSIBLE_COLLECTIONS_PATH': to_native(os.pathsep.join(AnsibleCollectionConfig.collection_paths)),
        'ANSIBLE_CONNECTION_PLUGINS': connection_loader.print_paths(),
        'ANSIBLE_HTTPAPI_PLUGINS': httpapi_loader.print_paths(),
        'ANSIBLE_NETCONF_PLUGINS': netconf_loader.print_paths(),
        'ANSIBLE_TERMINAL_PLUGINS': terminal_loader.print_paths(),
    })
    verbosity = []
    if display.verbosity:
        verbosity.append('-%s' % ('v' * display.verbosity))

    if not (cli_stub_path := C.config.get_config_value('_ANSIBLE_CONNECTION_PATH')):
        cli_stub_path = str(pathlib.Path(scripts.__file__).parent / CLI_STUB_NAME)

    p = subprocess.Popen(
        [sys.executable, cli_stub_path, *verbosity, to_text(os.getppid()), to_text(task_uuid)],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env,
    )

    write_to_stream(p.stdin, options)
    write_to_stream(p.stdin, play_context.dump_attrs())

    (stdout, stderr) = p.communicate()

    if p.returncode == 0:
        result = json.loads(to_text(stdout, errors='surrogate_then_replace'))
    else:
        try:
            result = json.loads(to_text(stderr, errors='surrogate_then_replace'))
        except json.decoder.JSONDecodeError:
            result = {'error': to_text(stderr, errors='surrogate_then_replace')}

    if 'messages' in result:
        for level, message in result['messages']:
            if level == 'log':
                display.display(message, log_only=True)
            elif level in ('debug', 'v', 'vv', 'vvv', 'vvvv', 'vvvvv', 'vvvvvv'):
                getattr(display, level)(message, host=play_context.remote_addr)
            else:
                if hasattr(display, level):
                    getattr(display, level)(message)
                else:
                    display.vvvv(message, host=play_context.remote_addr)

    if 'error' in result:
        if display.verbosity > 2:
            if result.get('exception'):
                msg = "The full traceback is:\n" + result['exception']
                display.display(msg, color=C.COLOR_ERROR)
        raise AnsibleError(result['error'])

    return result['socket_path']