def main(args=None):
    """ Called to initiate the connect to the remote device
    """

    parser = opt_help.create_base_parser(prog=None)
    opt_help.add_verbosity_options(parser)
    parser.add_argument('playbook_pid')
    parser.add_argument('task_uuid')
    args = parser.parse_args(args[1:] if args is not None else args)
    init_plugin_loader()

    # initialize verbosity
    display.verbosity = args.verbosity

    rc = 0
    result = {}
    messages = list()
    socket_path = None

    # Need stdin as a byte stream
    stdin = sys.stdin.buffer

    # Note: update the below log capture code after Display.display() is refactored.
    saved_stdout = sys.stdout
    sys.stdout = io.StringIO()

    try:
        # read the play context data via stdin, which means depickling it
        opts_data = read_stream(stdin)
        init_data = read_stream(stdin)

        pc_data = pickle.loads(init_data, encoding='bytes')
        options = pickle.loads(opts_data, encoding='bytes')

        play_context = PlayContext()
        play_context.from_attrs(pc_data)

    except Exception as e:
        rc = 1
        result.update({
            'error': to_text(e),
            'exception': traceback.format_exc()
        })

    if rc == 0:
        ssh = connection_loader.get('ssh', class_only=True)
        ansible_playbook_pid = args.playbook_pid
        task_uuid = args.task_uuid
        cp = ssh._create_control_path(play_context.remote_addr, play_context.port, play_context.remote_user, play_context.connection, ansible_playbook_pid)
        # create the persistent connection dir if need be and create the paths
        # which we will be using later
        tmp_path = unfrackpath(C.PERSISTENT_CONTROL_PATH_DIR)
        makedirs_safe(tmp_path)

        socket_path = unfrackpath(cp % dict(directory=tmp_path))
        lock_path = unfrackpath("%s/.ansible_pc_lock_%s" % os.path.split(socket_path))

        with file_lock(lock_path):
            if not os.path.exists(socket_path):
                messages.append(('vvvv', 'local domain socket does not exist, starting it'))
                original_path = os.getcwd()
                r, w = os.pipe()
                pid = fork_process()

                if pid == 0:
                    try:
                        os.close(r)
                        wfd = os.fdopen(w, 'w')
                        process = ConnectionProcess(wfd, play_context, socket_path, original_path, task_uuid, ansible_playbook_pid)
                        process.start(options)
                    except Exception:
                        messages.append(('error', traceback.format_exc()))
                        rc = 1

                    if rc == 0:
                        process.run()
                    else:
                        process.shutdown()

                    sys.exit(rc)

                else:
                    os.close(w)
                    rfd = os.fdopen(r, 'r')
                    data = json.loads(rfd.read(), cls=_tagless.Decoder)
                    messages.extend(data.pop('messages'))
                    result.update(data)

            else:
                messages.append(('vvvv', 'found existing local domain socket, using it!'))
                conn = Connection(socket_path)
                try:
                    conn.set_options(direct=options)
                except ConnectionError as exc:
                    messages.append(('debug', to_text(exc)))
                    raise ConnectionError('Unable to decode JSON from response set_options. See the debug log for more information.')
                pc_data = to_text(init_data)
                try:
                    conn.update_play_context(pc_data)
                    conn.set_check_prompt(task_uuid)
                except Exception as exc:
                    # Only network_cli has update_play context and set_check_prompt, so missing this is
                    # not fatal e.g. netconf
                    if isinstance(exc, ConnectionError) and getattr(exc, 'code', None) == -32601:
                        pass
                    else:
                        result.update({
                            'error': to_text(exc),
                            'exception': traceback.format_exc()
                        })

    if os.path.exists(socket_path):
        messages.extend(Connection(socket_path).pop_messages())
    messages.append(('vvvv', sys.stdout.getvalue()))
    result.update({
        'messages': messages,
        'socket_path': socket_path
    })

    sys.stdout = saved_stdout
    if 'exception' in result:
        rc = 1
        sys.stderr.write(json.dumps(result, cls=_tagless.Encoder))
    else:
        rc = 0
        sys.stdout.write(json.dumps(result, cls=_tagless.Encoder))

    sys.exit(rc)