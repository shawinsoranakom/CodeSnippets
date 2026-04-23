def test_openssl111_deprecations(self):
        options = [
            ssl.OP_NO_TLSv1,
            ssl.OP_NO_TLSv1_1,
            ssl.OP_NO_TLSv1_2,
            ssl.OP_NO_TLSv1_3
        ]
        protocols = []
        if hasattr(ssl, 'PROTOCOL_TLSv1'):
            protocols.append(ssl.PROTOCOL_TLSv1)
        if hasattr(ssl, 'PROTOCOL_TLSv1_1'):
            protocols.append(ssl.PROTOCOL_TLSv1_1)
        if hasattr(ssl, 'PROTOCOL_TLSv1_2'):
            protocols.append(ssl.PROTOCOL_TLSv1_2)
        protocols.append(ssl.PROTOCOL_TLS)
        versions = [
            ssl.TLSVersion.SSLv3,
            ssl.TLSVersion.TLSv1,
            ssl.TLSVersion.TLSv1_1,
        ]

        for option in options:
            with self.subTest(option=option):
                ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
                with self.assertWarns(DeprecationWarning) as cm:
                    ctx.options |= option
                self.assertEqual(
                    'ssl.OP_NO_SSL*/ssl.OP_NO_TLS* options are deprecated',
                    str(cm.warning)
                )

        for protocol in protocols:
            if not has_tls_protocol(protocol):
                continue
            with self.subTest(protocol=protocol):
                with self.assertWarns(DeprecationWarning) as cm:
                    ssl.SSLContext(protocol)
                self.assertEqual(
                    f'ssl.{protocol.name} is deprecated',
                    str(cm.warning)
                )

        for version in versions:
            if not has_tls_version(version):
                continue
            with self.subTest(version=version):
                ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
                with self.assertWarns(DeprecationWarning) as cm:
                    ctx.minimum_version = version
                version_text = '%s.%s' % (version.__class__.__name__, version.name)
                self.assertEqual(
                    f'ssl.{version_text} is deprecated',
                    str(cm.warning)
                )