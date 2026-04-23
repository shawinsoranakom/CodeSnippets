def find_py(cls):
        py_exe = None
        if sysconfig.is_python_build():
            py_exe = Path(sys.executable).parent / PY_EXE
        else:
            for p in os.getenv("PATH").split(";"):
                if p:
                    py_exe = Path(p) / PY_EXE
                    if py_exe.is_file():
                        break
            else:
                py_exe = None

        # Test launch and check version, to exclude installs of older
        # releases when running outside of a source tree
        if py_exe:
            try:
                with subprocess.Popen(
                    [py_exe, "-h"],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    encoding="ascii",
                    errors="ignore",
                ) as p:
                    p.stdin.close()
                    version = next(p.stdout, "\n").splitlines()[0].rpartition(" ")[2]
                    p.stdout.read()
                    p.wait(10)
                if not sys.version.startswith(version):
                    py_exe = None
            except OSError:
                py_exe = None

        if not py_exe:
            raise unittest.SkipTest(
                "cannot locate '{}' for test".format(PY_EXE)
            )
        return py_exe