def test_errors(self):
        self.assertRaises(TypeError, grp.getgrgid)
        self.assertRaises(TypeError, grp.getgrgid, 3.14)
        self.assertRaises(TypeError, grp.getgrnam)
        self.assertRaises(TypeError, grp.getgrnam, 42)
        self.assertRaises(TypeError, grp.getgrall, 42)
        # embedded null character
        self.assertRaisesRegex(ValueError, 'null', grp.getgrnam, 'a\x00b')

        # try to get some errors
        bynames = {}
        bygids = {}
        for (n, p, g, mem) in grp.getgrall():
            if not n or n == '+':
                continue # skip NIS entries etc.
            bynames[n] = g
            bygids[g] = n

        allnames = list(bynames.keys())
        namei = 0
        fakename = allnames[namei]
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

        self.assertRaises(KeyError, grp.getgrnam, fakename)

        # Choose a non-existent gid.
        fakegid = 4127
        while fakegid in bygids:
            fakegid = (fakegid * 3) % 0x10000

        self.assertRaises(KeyError, grp.getgrgid, fakegid)