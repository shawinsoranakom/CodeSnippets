def test_propagates_unbuffered_from_parent(self):
        for args in ("-u", "-Iuv"):
            with self.subTest(args=args):
                with mock.patch.dict(os.environ, {}, clear=True):
                    with tempfile.TemporaryDirectory() as d:
                        script = Path(d) / "manage.py"
                        script.touch()
                        mock_call = self.patch_autoreload([str(script), "runserver"])
                        with (
                            mock.patch("__main__.__spec__", None),
                            mock.patch.object(
                                autoreload.sys,
                                "orig_argv",
                                [self.executable, args, str(script), "runserver"],
                            ),
                        ):
                            autoreload.restart_with_reloader()
                    env = mock_call.call_args.kwargs["env"]
                    self.assertEqual(env.get("PYTHONUNBUFFERED"), "1")