def test_no_leaking(self):
        # Make sure we leak no resources
        if not mswindows:
            max_handles = 1026 # too much for most UNIX systems
        else:
            max_handles = 2050 # too much for (at least some) Windows setups
        if resource:
            # And if it is not too much, try to make it too much.
            try:
                soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
                if soft > 1024:
                    resource.setrlimit(resource.RLIMIT_NOFILE, (1024, hard))
                    self.addCleanup(resource.setrlimit, resource.RLIMIT_NOFILE,
                                    (soft, hard))
            except (OSError, ValueError):
                pass
        handles = []
        tmpdir = tempfile.mkdtemp()
        try:
            for i in range(max_handles):
                try:
                    tmpfile = os.path.join(tmpdir, os_helper.TESTFN)
                    handles.append(os.open(tmpfile, os.O_WRONLY|os.O_CREAT))
                except OSError as e:
                    if e.errno != errno.EMFILE:
                        raise
                    break
            else:
                self.skipTest("failed to reach the file descriptor limit "
                    "(tried %d)" % max_handles)
            # Close a couple of them (should be enough for a subprocess).
            # Close lower file descriptors, so select() will work.
            handles.reverse()
            for i in range(10):
                os.close(handles.pop())
            # Loop creating some subprocesses. If one of them leaks some fds,
            # the next loop iteration will fail by reaching the max fd limit.
            for i in range(15):
                p = subprocess.Popen([sys.executable, "-c",
                                      "import sys;"
                                      "sys.stdout.write(sys.stdin.read())"],
                                     stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE)
                data = p.communicate(b"lime")[0]
                self.assertEqual(data, b"lime")
        finally:
            for h in handles:
                os.close(h)
            shutil.rmtree(tmpdir)