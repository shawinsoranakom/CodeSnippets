def test_virtualenv_in_list(self):
        with self.fake_venv() as (venv_exe, env):
            data = self.run_py(["-0p"], env=env)
            for line in data["stdout"].splitlines():
                m = re.match(r"\s*\*\s+(.+)$", line)
                if m:
                    self.assertEqual(str(venv_exe), m.group(1))
                    break
            else:
                if support.verbose:
                    print(data["stdout"])
                    print(data["stderr"])
                self.fail("did not find active venv path")

            data = self.run_py(["-0"], env=env)
            for line in data["stdout"].splitlines():
                m = re.match(r"\s*\*\s+(.+)$", line)
                if m:
                    self.assertEqual("Active venv", m.group(1))
                    break
            else:
                self.fail("did not find active venv entry")