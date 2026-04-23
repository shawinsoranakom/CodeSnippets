def testGetaddrinfo(self):
        try:
            socket.getaddrinfo('localhost', 80)
        except socket.gaierror as err:
            if err.errno == socket.EAI_SERVICE:
                # see http://bugs.python.org/issue1282647
                self.skipTest("buggy libc version")
            raise
        # len of every sequence is supposed to be == 5
        for info in socket.getaddrinfo(HOST, None):
            self.assertEqual(len(info), 5)
        # host can be a domain name, a string representation of an
        # IPv4/v6 address or None
        socket.getaddrinfo('localhost', 80)
        socket.getaddrinfo('127.0.0.1', 80)
        socket.getaddrinfo(None, 80)
        if socket_helper.IPV6_ENABLED:
            socket.getaddrinfo('::1', 80)
        # port can be a string service name such as "http", a numeric
        # port number or None
        # Issue #26936: this fails on Android before API level 23.
        if not (support.is_android and platform.android_ver().api_level < 23):
            socket.getaddrinfo(HOST, "http")
        socket.getaddrinfo(HOST, 80)
        socket.getaddrinfo(HOST, None)
        # test family and socktype filters
        infos = socket.getaddrinfo(HOST, 80, socket.AF_INET, socket.SOCK_STREAM)
        for family, type, _, _, _ in infos:
            self.assertEqual(family, socket.AF_INET)
            self.assertEqual(repr(family), '<AddressFamily.AF_INET: %r>' % family.value)
            self.assertEqual(str(family), str(family.value))
            self.assertEqual(type, socket.SOCK_STREAM)
            self.assertEqual(repr(type), '<SocketKind.SOCK_STREAM: %r>' % type.value)
            self.assertEqual(str(type), str(type.value))
        infos = socket.getaddrinfo(HOST, None, 0, socket.SOCK_STREAM)
        for _, socktype, _, _, _ in infos:
            self.assertEqual(socktype, socket.SOCK_STREAM)
        # test proto and flags arguments
        socket.getaddrinfo(HOST, None, 0, 0, socket.SOL_TCP)
        socket.getaddrinfo(HOST, None, 0, 0, 0, socket.AI_PASSIVE)
        # a server willing to support both IPv4 and IPv6 will
        # usually do this
        socket.getaddrinfo(None, 0, socket.AF_UNSPEC, socket.SOCK_STREAM, 0,
                           socket.AI_PASSIVE)
        # test keyword arguments
        a = socket.getaddrinfo(HOST, None)
        b = socket.getaddrinfo(host=HOST, port=None)
        self.assertEqual(a, b)
        a = socket.getaddrinfo(HOST, None, socket.AF_INET)
        b = socket.getaddrinfo(HOST, None, family=socket.AF_INET)
        self.assertEqual(a, b)
        a = socket.getaddrinfo(HOST, None, 0, socket.SOCK_STREAM)
        b = socket.getaddrinfo(HOST, None, type=socket.SOCK_STREAM)
        self.assertEqual(a, b)
        a = socket.getaddrinfo(HOST, None, 0, 0, socket.SOL_TCP)
        b = socket.getaddrinfo(HOST, None, proto=socket.SOL_TCP)
        self.assertEqual(a, b)
        a = socket.getaddrinfo(HOST, None, 0, 0, 0, socket.AI_PASSIVE)
        b = socket.getaddrinfo(HOST, None, flags=socket.AI_PASSIVE)
        self.assertEqual(a, b)
        a = socket.getaddrinfo(None, 0, socket.AF_UNSPEC, socket.SOCK_STREAM, 0,
                               socket.AI_PASSIVE)
        b = socket.getaddrinfo(host=None, port=0, family=socket.AF_UNSPEC,
                               type=socket.SOCK_STREAM, proto=0,
                               flags=socket.AI_PASSIVE)
        self.assertEqual(a, b)
        # Issue #6697.
        self.assertRaises(UnicodeEncodeError, socket.getaddrinfo, 'localhost', '\uD800')

        if hasattr(socket, 'AI_NUMERICSERV'):
            self.assertRaises(socket.gaierror, socket.getaddrinfo, "localhost", "http",
                              flags=socket.AI_NUMERICSERV)

            # Issue 17269: test workaround for OS X platform bug segfault
            try:
                # The arguments here are undefined and the call may succeed
                # or fail.  All we care here is that it doesn't segfault.
                socket.getaddrinfo("localhost", None, 0, 0, 0,
                                   socket.AI_NUMERICSERV)
            except socket.gaierror:
                pass