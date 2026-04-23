def run_py(self, args, env=None, allow_fail=False, expect_returncode=0, argv=None):
        if not self.py_exe:
            self.py_exe = self.find_py()

        ignore = {"VIRTUAL_ENV", "PY_PYTHON", "PY_PYTHON2", "PY_PYTHON3"}
        env = {
            **{k.upper(): v for k, v in os.environ.items() if k.upper() not in ignore},
            "PYLAUNCHER_DEBUG": "1",
            "PYLAUNCHER_DRYRUN": "1",
            "PYLAUNCHER_LIMIT_TO_COMPANY": "",
            **{k.upper(): v for k, v in (env or {}).items()},
        }
        if ini_dir := getattr(self, '_ini_dir', None):
            env.setdefault("_PYLAUNCHER_INIDIR", ini_dir)
        if not argv:
            argv = [self.py_exe, *args]
        with subprocess.Popen(
            argv,
            env=env,
            executable=self.py_exe,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        ) as p:
            p.stdin.close()
            p.wait(10)
            out = p.stdout.read().decode("utf-8", "replace")
            err = p.stderr.read().decode("ascii", "replace").replace("\uFFFD", "?")
        if p.returncode != expect_returncode and support.verbose and not allow_fail:
            print("++ COMMAND ++")
            print([self.py_exe, *args])
            print("++ STDOUT ++")
            print(out)
            print("++ STDERR ++")
            print(err)
        if allow_fail and p.returncode != expect_returncode:
            raise subprocess.CalledProcessError(p.returncode, [self.py_exe, *args], out, err)
        else:
            self.assertEqual(expect_returncode, p.returncode)
        data = {
            s.partition(":")[0]: s.partition(":")[2].lstrip()
            for s in err.splitlines()
            if not s.startswith("#") and ":" in s
        }
        data["stdout"] = out
        data["stderr"] = err
        return data