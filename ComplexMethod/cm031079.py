def run_python(self, argv, *, cwd=None):
        # This method is inspired by
        # EmbeddingTestsMixin.run_embedded_interpreter() in test_embed.py.
        import shlex
        import subprocess
        if isinstance(argv, str):
            argv = shlex.split(argv)
        argv = [sys.executable, *argv]
        try:
            proc = subprocess.run(
                argv,
                cwd=cwd,
                capture_output=True,
                text=True,
            )
        except Exception as exc:
            self.debug(f'# cmd: {shlex.join(argv)}')
            if isinstance(exc, FileNotFoundError) and not exc.filename:
                if os.path.exists(argv[0]):
                    exists = 'exists'
                else:
                    exists = 'does not exist'
                self.debug(f'{argv[0]} {exists}')
            raise  # re-raise
        assert proc.stderr == '' or proc.returncode != 0, proc.stderr
        if proc.returncode != 0 and support.verbose:
            self.debug(f'# python3 {shlex.join(argv[1:])} failed:')
            self.debug(proc.stdout, header='stdout')
            self.debug(proc.stderr, header='stderr')
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stderr, '')
        return proc.stdout