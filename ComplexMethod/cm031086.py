def test_getgroups(self):
        with os.popen('id -G 2>/dev/null') as idg:
            groups = idg.read().strip()
            ret = idg.close()

        try:
            idg_groups = set(int(g) for g in groups.split())
        except ValueError:
            idg_groups = set()
        if ret is not None or not idg_groups:
            raise unittest.SkipTest("need working 'id -G'")

        # Issues 16698: OS X ABIs prior to 10.6 have limits on getgroups()
        if sys.platform == 'darwin':
            import sysconfig
            dt = sysconfig.get_config_var('MACOSX_DEPLOYMENT_TARGET') or '10.3'
            if tuple(int(n) for n in dt.split('.')[0:2]) < (10, 6):
                raise unittest.SkipTest("getgroups(2) is broken prior to 10.6")

        # 'id -G' and 'os.getgroups()' should return the same
        # groups, ignoring order, duplicates, and the effective gid.
        # #10822/#26944 - It is implementation defined whether
        # posix.getgroups() includes the effective gid.
        symdiff = idg_groups.symmetric_difference(posix.getgroups())
        self.assertTrue(not symdiff or symdiff == {posix.getegid()})