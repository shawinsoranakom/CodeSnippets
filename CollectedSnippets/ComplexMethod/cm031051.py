def _run_repl_globals_test(self, expectations, *, as_file=False, as_module=False, pythonstartup=False):
        clean_env = make_clean_env()
        clean_env["NO_COLOR"] = "1"  # force_not_colorized doesn't touch subprocesses

        with tempfile.TemporaryDirectory() as td:
            blue = pathlib.Path(td) / "blue"
            blue.mkdir()
            mod = blue / "calx.py"
            mod.write_text("FOO = 42", encoding="utf-8")
            startup = blue / "startup.py"
            startup.write_text("BAR = 64", encoding="utf-8")
            commands = [
                "print(f'^{" + var + "=}')" for var in expectations
            ] + ["exit()"]
            if pythonstartup:
                clean_env["PYTHONSTARTUP"] = str(startup)
            if as_file and as_module:
                self.fail("as_file and as_module are mutually exclusive")
            elif as_file:
                output, exit_code = self.run_repl(
                    commands,
                    cmdline_args=[str(mod)],
                    env=clean_env,
                    skip=True,
                )
            elif as_module:
                output, exit_code = self.run_repl(
                    commands,
                    cmdline_args=["-m", "blue.calx"],
                    env=clean_env,
                    cwd=td,
                    skip=True,
                )
            else:
                output, exit_code = self.run_repl(
                    commands,
                    cmdline_args=[],
                    env=clean_env,
                    cwd=td,
                    skip=True,
                )

        self.assertEqual(exit_code, 0)
        for var, expected in expectations.items():
            with self.subTest(var=var, expected=expected):
                if m := re.search(rf"\^{var}=(.+?)[\r\n]", output):
                    self._assertMatchOK(var, expected, actual=m.group(1))
                else:
                    self.fail(f"{var}= not found in output: {output!r}\n\n{output}")

        self.assertNotIn("Exception", output)
        self.assertNotIn("Traceback", output)