def test_getaddrinfo_int_port_overflow(self):
        # gh-74895: Test that getaddrinfo does not raise OverflowError on port.
        #
        # POSIX getaddrinfo() never specify the valid range for "service"
        # decimal port number values. For IPv4 and IPv6 they are technically
        # unsigned 16-bit values, but the API is protocol agnostic. Which values
        # trigger an error from the C library function varies by platform as
        # they do not all perform validation.

        # The key here is that we don't want to produce OverflowError as Python
        # prior to 3.12 did for ints outside of a [LONG_MIN, LONG_MAX] range.
        # Leave the error up to the underlying string based platform C API.

        from _testcapi import ULONG_MAX, LONG_MAX, LONG_MIN
        try:
            socket.getaddrinfo(None, ULONG_MAX + 1, type=socket.SOCK_STREAM)
        except OverflowError:
            # Platforms differ as to what values constitute a getaddrinfo() error
            # return. Some fail for LONG_MAX+1, others ULONG_MAX+1, and Windows
            # silently accepts such huge "port" aka "service" numeric values.
            self.fail("Either no error or socket.gaierror expected.")
        except socket.gaierror:
            pass

        try:
            socket.getaddrinfo(None, LONG_MAX + 1, type=socket.SOCK_STREAM)
        except OverflowError:
            self.fail("Either no error or socket.gaierror expected.")
        except socket.gaierror:
            pass

        try:
            socket.getaddrinfo(None, LONG_MAX - 0xffff + 1, type=socket.SOCK_STREAM)
        except OverflowError:
            self.fail("Either no error or socket.gaierror expected.")
        except socket.gaierror:
            pass

        try:
            socket.getaddrinfo(None, LONG_MIN - 1, type=socket.SOCK_STREAM)
        except OverflowError:
            self.fail("Either no error or socket.gaierror expected.")
        except socket.gaierror:
            pass

        socket.getaddrinfo(None, 0, type=socket.SOCK_STREAM)  # No error expected.
        socket.getaddrinfo(None, 0xffff, type=socket.SOCK_STREAM)