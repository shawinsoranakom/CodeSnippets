def test_errors(self):
        self.assertRaises(TypeError, pwd.getpwuid)
        self.assertRaises(TypeError, pwd.getpwuid, 3.14)
        self.assertRaises(TypeError, pwd.getpwnam)
        self.assertRaises(TypeError, pwd.getpwnam, 42)
        self.assertRaises(TypeError, pwd.getpwall, 42)
        # embedded null character
        self.assertRaisesRegex(ValueError, 'null', pwd.getpwnam, 'a\x00b')

        # try to get some errors
        bynames = {}
        byuids = {}
        for (n, p, u, g, gecos, d, s) in pwd.getpwall():
            bynames[n] = u
            byuids[u] = n

        allnames = list(bynames.keys())
        namei = 0
        fakename = allnames[namei] if allnames else "invaliduser"
        while fakename in bynames:
            chars = list(fakename)
            for i in range(len(chars)):
                if chars[i] == 'z':
                    chars[i] = 'A'
                    break
                elif chars[i] == 'Z':
                    continue
                else:
                    chars[i] = chr(ord(chars[i]) + 1)
                    break
            else:
                namei = namei + 1
                try:
                    fakename = allnames[namei]
                except IndexError:
                    # should never happen... if so, just forget it
                    break
            fakename = ''.join(chars)

        self.assertRaises(KeyError, pwd.getpwnam, fakename)

        # In some cases, byuids isn't a complete list of all users in the
        # system, so if we try to pick a value not in byuids (via a perturbing
        # loop, say), pwd.getpwuid() might still be able to find data for that
        # uid. Using sys.maxint may provoke the same problems, but hopefully
        # it will be a more repeatable failure.
        fakeuid = sys.maxsize
        self.assertNotIn(fakeuid, byuids)
        self.assertRaises(KeyError, pwd.getpwuid, fakeuid)

        # -1 shouldn't be a valid uid because it has a special meaning in many
        # uid-related functions
        self.assertRaises(KeyError, pwd.getpwuid, -1)
        # should be out of uid_t range
        self.assertRaises(KeyError, pwd.getpwuid, 2**128)
        self.assertRaises(KeyError, pwd.getpwuid, -2**128)