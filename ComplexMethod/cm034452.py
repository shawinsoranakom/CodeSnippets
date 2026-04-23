def main():

    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type='str', default='127.0.0.1'),
            timeout=dict(type='int', default=300),
            connect_timeout=dict(type='int', default=5),
            delay=dict(type='int', default=0),
            port=dict(type='int'),
            active_connection_states=dict(type='list', elements='str', default=['ESTABLISHED', 'FIN_WAIT1', 'FIN_WAIT2', 'SYN_RECV', 'SYN_SENT', 'TIME_WAIT']),
            path=dict(type='path'),
            search_regex=dict(type='str'),
            state=dict(type='str', default='started', choices=['absent', 'drained', 'present', 'started', 'stopped']),
            exclude_hosts=dict(type='list', elements='str'),
            sleep=dict(type='int', default=1),
            msg=dict(type='str'),
        ),
    )

    host = module.params['host']
    timeout = module.params['timeout']
    connect_timeout = module.params['connect_timeout']
    delay = module.params['delay']
    port = module.params['port']
    state = module.params['state']

    path = module.params['path']
    b_path = to_bytes(path, errors='surrogate_or_strict', nonstring='passthru')

    search_regex = module.params['search_regex']
    b_search_regex = to_bytes(search_regex, errors='surrogate_or_strict', nonstring='passthru')

    msg = module.params['msg']

    if search_regex is not None:
        try:
            b_compiled_search_re = re.compile(b_search_regex, re.MULTILINE)
        except re.error as e:
            module.fail_json(msg="Invalid regular expression: %s" % e)
    else:
        b_compiled_search_re = None

    match_groupdict = {}
    match_groups = ()

    if port and path:
        module.fail_json(msg="port and path parameter can not both be passed to wait_for", elapsed=0)
    if path and state == 'stopped':
        module.fail_json(msg="state=stopped should only be used for checking a port in the wait_for module", elapsed=0)
    if path and state == 'drained':
        module.fail_json(msg="state=drained should only be used for checking a port in the wait_for module", elapsed=0)
    if module.params['exclude_hosts'] is not None and state != 'drained':
        module.fail_json(msg="exclude_hosts should only be with state=drained", elapsed=0)
    for _connection_state in module.params['active_connection_states']:
        try:
            get_connection_state_id(_connection_state)
        except Exception:
            module.fail_json(msg="unknown active_connection_state (%s) defined" % _connection_state, elapsed=0)

    start = datetime.now(timezone.utc)

    if delay:
        time.sleep(delay)

    if not port and not path and state != 'drained':
        time.sleep(timeout)
    elif state in ['absent', 'stopped']:
        # first wait for the stop condition
        end = start + timedelta(seconds=timeout)

        while datetime.now(timezone.utc) < end:
            if path:
                try:
                    if not os.access(b_path, os.F_OK):
                        break
                except OSError:
                    break
            elif port:
                try:
                    s = socket.create_connection((host, port), connect_timeout)
                    s.shutdown(socket.SHUT_RDWR)
                    s.close()
                except Exception:
                    break
            # Conditions not yet met, wait and try again
            time.sleep(module.params['sleep'])
        else:
            elapsed = datetime.now(timezone.utc) - start
            if port:
                module.fail_json(msg=msg or "Timeout when waiting for %s:%s to stop." % (host, port), elapsed=elapsed.seconds)
            elif path:
                module.fail_json(msg=msg or "Timeout when waiting for %s to be absent." % (path), elapsed=elapsed.seconds)

    elif state in ['started', 'present']:
        # wait for start condition
        end = start + timedelta(seconds=timeout)
        while datetime.now(timezone.utc) < end:
            if path:
                try:
                    os.stat(b_path)
                except OSError as e:
                    # If anything except file not present, throw an error
                    if e.errno != 2:
                        elapsed = datetime.now(timezone.utc) - start
                        module.fail_json(msg=msg or "Failed to stat %s, %s" % (path, e.strerror), elapsed=elapsed.seconds)
                    # file doesn't exist yet, so continue
                else:
                    # File exists.  Are there additional things to check?
                    if not b_compiled_search_re:
                        # nope, succeed!
                        break

                    try:
                        with open(b_path, 'rb') as f:
                            try:
                                with contextlib.closing(mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)) as mm:
                                    search = b_compiled_search_re.search(mm)
                                    if search:
                                        if search.groupdict():
                                            match_groupdict = search.groupdict()
                                        if search.groups():
                                            match_groups = search.groups()
                                        break
                            except (ValueError, OSError) as e:
                                module.debug('wait_for failed to use mmap on "%s": %s. Falling back to file read().' % (path, to_native(e)))
                                # cannot mmap this file, try normal read
                                search = re.search(b_compiled_search_re, f.read())
                                if search:
                                    if search.groupdict():
                                        match_groupdict = search.groupdict()
                                    if search.groups():
                                        match_groups = search.groups()
                                    break
                            except Exception as e:
                                module.warn('wait_for failed on "%s", unexpected exception(%s): %s.).' % (path, to_native(e.__class__), to_native(e)))
                    except OSError:
                        pass
            elif port:
                alt_connect_timeout = math.ceil(
                    _timedelta_total_seconds(end - datetime.now(timezone.utc)),
                )
                try:
                    s = socket.create_connection((host, int(port)), min(connect_timeout, alt_connect_timeout))
                except Exception:
                    # Failed to connect by connect_timeout. wait and try again
                    pass
                else:
                    # Connected -- are there additional conditions?
                    if b_compiled_search_re:
                        b_data = b''
                        matched = False
                        while datetime.now(timezone.utc) < end:
                            max_timeout = math.ceil(
                                _timedelta_total_seconds(
                                    end - datetime.now(timezone.utc),
                                ),
                            )
                            readable = select.select([s], [], [], max_timeout)[0]
                            if not readable:
                                # No new data.  Probably means our timeout
                                # expired
                                continue
                            response = s.recv(1024)
                            if not response:
                                # Server shutdown
                                break
                            b_data += response
                            if b_compiled_search_re.search(b_data):
                                matched = True
                                break

                        # Shutdown the client socket
                        try:
                            s.shutdown(socket.SHUT_RDWR)
                        except OSError as ex:
                            if ex.errno != errno.ENOTCONN:
                                raise
                        # else, the server broke the connection on its end, assume it's not ready
                        else:
                            s.close()
                        if matched:
                            # Found our string, success!
                            break
                    else:
                        # Connection established, success!
                        try:
                            s.shutdown(socket.SHUT_RDWR)
                        except OSError as ex:
                            if ex.errno != errno.ENOTCONN:
                                raise
                        # else, the server broke the connection on its end, assume it's not ready
                        else:
                            s.close()
                        break

            # Conditions not yet met, wait and try again
            time.sleep(module.params['sleep'])

        else:   # while-else
            # Timeout expired
            elapsed = datetime.now(timezone.utc) - start
            if port:
                if search_regex:
                    module.fail_json(msg=msg or "Timeout when waiting for search string %s in %s:%s" % (search_regex, host, port), elapsed=elapsed.seconds)
                else:
                    module.fail_json(msg=msg or "Timeout when waiting for %s:%s" % (host, port), elapsed=elapsed.seconds)
            elif path:
                if search_regex:
                    module.fail_json(msg=msg or "Timeout when waiting for search string %s in %s" % (search_regex, path), elapsed=elapsed.seconds)
                else:
                    module.fail_json(msg=msg or "Timeout when waiting for file %s" % (path), elapsed=elapsed.seconds)

    elif state == 'drained':
        # wait until all active connections are gone
        end = start + timedelta(seconds=timeout)
        tcpconns = TCPConnectionInfo(module)
        while datetime.now(timezone.utc) < end:
            if tcpconns.get_active_connections_count() == 0:
                break

            # Conditions not yet met, wait and try again
            time.sleep(module.params['sleep'])
        else:
            elapsed = datetime.now(timezone.utc) - start
            module.fail_json(msg=msg or "Timeout when waiting for %s:%s to drain" % (host, port), elapsed=elapsed.seconds)

    elapsed = datetime.now(timezone.utc) - start
    module.exit_json(state=state, port=port, search_regex=search_regex, match_groups=match_groups, match_groupdict=match_groupdict, path=path,
                     elapsed=elapsed.seconds)