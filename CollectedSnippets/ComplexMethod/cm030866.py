def test_PROTOCOL_TLS(self):
        """Connecting to an SSLv23 server with various client options"""
        if support.verbose:
            sys.stdout.write("\n")
        if has_tls_version('SSLv3'):
            try_protocol_combo(ssl.PROTOCOL_TLS, ssl.PROTOCOL_SSLv3, False)
        try_protocol_combo(ssl.PROTOCOL_TLS, ssl.PROTOCOL_TLS, True)
        if has_tls_version('TLSv1'):
            try_protocol_combo(ssl.PROTOCOL_TLS, ssl.PROTOCOL_TLSv1, 'TLSv1')

        if has_tls_version('SSLv3'):
            try_protocol_combo(ssl.PROTOCOL_TLS, ssl.PROTOCOL_SSLv3, False, ssl.CERT_OPTIONAL)
        try_protocol_combo(ssl.PROTOCOL_TLS, ssl.PROTOCOL_TLS, True, ssl.CERT_OPTIONAL)
        if has_tls_version('TLSv1'):
            try_protocol_combo(ssl.PROTOCOL_TLS, ssl.PROTOCOL_TLSv1, 'TLSv1', ssl.CERT_OPTIONAL)

        if has_tls_version('SSLv3'):
            try_protocol_combo(ssl.PROTOCOL_TLS, ssl.PROTOCOL_SSLv3, False, ssl.CERT_REQUIRED)
        try_protocol_combo(ssl.PROTOCOL_TLS, ssl.PROTOCOL_TLS, True, ssl.CERT_REQUIRED)
        if has_tls_version('TLSv1'):
            try_protocol_combo(ssl.PROTOCOL_TLS, ssl.PROTOCOL_TLSv1, 'TLSv1', ssl.CERT_REQUIRED)

        # Server with specific SSL options
        if has_tls_version('SSLv3'):
            try_protocol_combo(ssl.PROTOCOL_TLS, ssl.PROTOCOL_SSLv3, False,
                           server_options=ssl.OP_NO_SSLv3)
        # Will choose TLSv1
        try_protocol_combo(ssl.PROTOCOL_TLS, ssl.PROTOCOL_TLS, True,
                           server_options=ssl.OP_NO_SSLv2 | ssl.OP_NO_SSLv3)
        if has_tls_version('TLSv1'):
            try_protocol_combo(ssl.PROTOCOL_TLS, ssl.PROTOCOL_TLSv1, False,
                               server_options=ssl.OP_NO_TLSv1)