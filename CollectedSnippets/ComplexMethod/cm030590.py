def testGetServBy(self):
        eq = self.assertEqual
        # Find one service that exists, then check all the related interfaces.
        # I've ordered this by protocols that have both a tcp and udp
        # protocol, at least for modern Linuxes.
        if (
            sys.platform.startswith(
                ('linux', 'android', 'freebsd', 'netbsd', 'gnukfreebsd'))
            or is_apple
        ):
            # avoid the 'echo' service on this platform, as there is an
            # assumption breaking non-standard port/protocol entry
            services = ('daytime', 'qotd', 'domain')
        else:
            services = ('echo', 'daytime', 'domain')
        for service in services:
            try:
                port = socket.getservbyname(service, 'tcp')
                break
            except OSError:
                pass
        else:
            raise OSError
        # Try same call with optional protocol omitted
        # Issue gh-71123: this fails on Android before API level 23.
        if not (support.is_android and platform.android_ver().api_level < 23):
            port2 = socket.getservbyname(service)
            eq(port, port2)
        # Try udp, but don't barf if it doesn't exist
        try:
            udpport = socket.getservbyname(service, 'udp')
        except OSError:
            udpport = None
        else:
            eq(udpport, port)
        # Now make sure the lookup by port returns the same service name
        # Issue #26936: when the protocol is omitted, this fails on Android
        # before API level 28.
        if not (support.is_android and platform.android_ver().api_level < 28):
            eq(socket.getservbyport(port2), service)
        eq(socket.getservbyport(port, 'tcp'), service)
        if udpport is not None:
            eq(socket.getservbyport(udpport, 'udp'), service)
        # Make sure getservbyport does not accept out of range ports.
        self.assertRaises(OverflowError, socket.getservbyport, -1)
        self.assertRaises(OverflowError, socket.getservbyport, 65536)