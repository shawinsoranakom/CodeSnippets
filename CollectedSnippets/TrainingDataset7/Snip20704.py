def test_crash_password_does_not_leak(self):
        # The password doesn't leak in an exception that results from a client
        # crash.
        args, env = self.settings_to_cmd_args_env({"PASSWORD": "somepassword"}, [])
        if env:
            env = {**os.environ, **env}
        fake_client = Path(__file__).with_name("fake_client.py")
        args[0:1] = [sys.executable, str(fake_client)]
        with self.assertRaises(subprocess.CalledProcessError) as ctx:
            subprocess.run(args, check=True, env=env)
        self.assertNotIn("somepassword", str(ctx.exception))