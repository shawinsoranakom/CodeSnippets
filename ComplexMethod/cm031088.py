def test_getcwd_long_path(self):
        # bpo-37412: On Linux, PATH_MAX is usually around 4096 bytes. On
        # Windows, MAX_PATH is defined as 260 characters, but Windows supports
        # longer path if longer paths support is enabled. Internally, the os
        # module uses MAXPATHLEN which is at least 1024.
        #
        # Use a directory name of 200 characters to fit into Windows MAX_PATH
        # limit.
        #
        # On Windows, the test can stop when trying to create a path longer
        # than MAX_PATH if long paths support is disabled:
        # see RtlAreLongPathsEnabled().
        min_len = 2000   # characters
        # On VxWorks, PATH_MAX is defined as 1024 bytes. Creating a path
        # longer than PATH_MAX will fail.
        if sys.platform == 'vxworks':
            min_len = 1000
        dirlen = 200     # characters
        dirname = 'python_test_dir_'
        dirname = dirname + ('a' * (dirlen - len(dirname)))

        with tempfile.TemporaryDirectory() as tmpdir:
            with os_helper.change_cwd(tmpdir) as path:
                expected = path

                while True:
                    cwd = os.getcwd()
                    self.assertEqual(cwd, expected)

                    need = min_len - (len(cwd) + len(os.path.sep))
                    if need <= 0:
                        break
                    if len(dirname) > need and need > 0:
                        dirname = dirname[:need]

                    path = os.path.join(path, dirname)
                    try:
                        os.mkdir(path)
                        # On Windows, chdir() can fail
                        # even if mkdir() succeeded
                        os.chdir(path)
                    except FileNotFoundError:
                        # On Windows, catch ERROR_PATH_NOT_FOUND (3) and
                        # ERROR_FILENAME_EXCED_RANGE (206) errors
                        # ("The filename or extension is too long")
                        break
                    except OSError as exc:
                        if exc.errno == errno.ENAMETOOLONG:
                            break
                        else:
                            raise

                    expected = path

                if support.verbose:
                    print(f"Tested current directory length: {len(cwd)}")