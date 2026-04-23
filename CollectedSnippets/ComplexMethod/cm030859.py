def server_params_test(client_context, server_context, indata=b"FOO\n",
                       chatty=True, connectionchatty=False, sni_name=None,
                       session=None):
    """
    Launch a server, connect a client to it and try various reads
    and writes.
    """
    stats = {}
    server = ThreadedEchoServer(context=server_context,
                                chatty=chatty,
                                connectionchatty=False)
    with server:
        with client_context.wrap_socket(socket.socket(),
                server_hostname=sni_name, session=session) as s:
            s.connect((HOST, server.port))
            for arg in [indata, bytearray(indata), memoryview(indata)]:
                if connectionchatty:
                    if support.verbose:
                        sys.stdout.write(
                            " client:  sending %r...\n" % indata)
                s.write(arg)
                outdata = s.read()
                if connectionchatty:
                    if support.verbose:
                        sys.stdout.write(" client:  read %r\n" % outdata)
                if outdata != indata.lower():
                    raise AssertionError(
                        "bad data <<%r>> (%d) received; expected <<%r>> (%d)\n"
                        % (outdata[:20], len(outdata),
                           indata[:20].lower(), len(indata)))
            s.write(b"over\n")
            if connectionchatty:
                if support.verbose:
                    sys.stdout.write(" client:  closing connection.\n")
            stats.update({
                'compression': s.compression(),
                'cipher': s.cipher(),
                'peercert': s.getpeercert(),
                'client_alpn_protocol': s.selected_alpn_protocol(),
                'version': s.version(),
                'session_reused': s.session_reused,
                'session': s.session,
            })
            if CAN_GET_SELECTED_OPENSSL_GROUP:
                stats.update({'group': s.group()})
            if CAN_GET_SELECTED_OPENSSL_SIGALG:
                stats.update({'client_sigalg': s.client_sigalg()})
                stats.update({'server_sigalg': s.server_sigalg()})
            s.close()
        stats['server_alpn_protocols'] = server.selected_alpn_protocols
        stats['server_shared_ciphers'] = server.shared_ciphers
    return stats