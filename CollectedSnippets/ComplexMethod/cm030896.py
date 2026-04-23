def test_list(self):
        # Change some metadata to None, then compare list() output
        # word-for-word. We want list() to not raise, and to only change
        # printout for the affected piece of metadata.
        # (n.b.: some contents of the test archive are hardcoded.)
        for attr_names in ({'mtime'}, {'mode'}, {'uid'}, {'gid'},
                           {'uname'}, {'gname'},
                           {'uid', 'uname'}, {'gid', 'gname'}):
            with (self.subTest(attr_names=attr_names),
                  tarfile.open(tarname, encoding="iso8859-1") as tar):
                tio_prev = io.TextIOWrapper(io.BytesIO(), 'ascii', newline='\n')
                with support.swap_attr(sys, 'stdout', tio_prev):
                    tar.list()
                for member in tar.getmembers():
                    for attr_name in attr_names:
                        setattr(member, attr_name, None)
                tio_new = io.TextIOWrapper(io.BytesIO(), 'ascii', newline='\n')
                with support.swap_attr(sys, 'stdout', tio_new):
                    tar.list()
                for expected, got in zip(tio_prev.detach().getvalue().split(),
                                         tio_new.detach().getvalue().split()):
                    if attr_names == {'mtime'} and re.match(rb'2003-01-\d\d', expected):
                        self.assertEqual(got, b'????-??-??')
                    elif attr_names == {'mtime'} and re.match(rb'\d\d:\d\d:\d\d', expected):
                        self.assertEqual(got, b'??:??:??')
                    elif attr_names == {'mode'} and re.match(
                            rb'.([r-][w-][x-]){3}', expected):
                        self.assertEqual(got, b'??????????')
                    elif attr_names == {'uname'} and expected.startswith(
                            (b'tarfile/', b'lars/', b'foo/')):
                        exp_user, exp_group = expected.split(b'/')
                        got_user, got_group = got.split(b'/')
                        self.assertEqual(got_group, exp_group)
                        self.assertRegex(got_user, b'[0-9]+')
                    elif attr_names == {'gname'} and expected.endswith(
                            (b'/tarfile', b'/users', b'/bar')):
                        exp_user, exp_group = expected.split(b'/')
                        got_user, got_group = got.split(b'/')
                        self.assertEqual(got_user, exp_user)
                        self.assertRegex(got_group, b'[0-9]+')
                    elif attr_names == {'uid'} and expected.startswith(
                            (b'1000/')):
                        exp_user, exp_group = expected.split(b'/')
                        got_user, got_group = got.split(b'/')
                        self.assertEqual(got_group, exp_group)
                        self.assertEqual(got_user, b'None')
                    elif attr_names == {'gid'} and expected.endswith((b'/100')):
                        exp_user, exp_group = expected.split(b'/')
                        got_user, got_group = got.split(b'/')
                        self.assertEqual(got_user, exp_user)
                        self.assertEqual(got_group, b'None')
                    elif attr_names == {'uid', 'uname'} and expected.startswith(
                            (b'tarfile/', b'lars/', b'foo/', b'1000/')):
                        exp_user, exp_group = expected.split(b'/')
                        got_user, got_group = got.split(b'/')
                        self.assertEqual(got_group, exp_group)
                        self.assertEqual(got_user, b'None')
                    elif attr_names == {'gname', 'gid'} and expected.endswith(
                            (b'/tarfile', b'/users', b'/bar', b'/100')):
                        exp_user, exp_group = expected.split(b'/')
                        got_user, got_group = got.split(b'/')
                        self.assertEqual(got_user, exp_user)
                        self.assertEqual(got_group, b'None')
                    else:
                        # In other cases the output should be the same
                        self.assertEqual(expected, got)