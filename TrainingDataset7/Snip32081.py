def test_python(self):
        cmd = shell.Command()
        mock_code = mock.Mock(interact=mock.MagicMock())
        options = {"verbosity": 0, "no_startup": True, "no_imports": False}

        with mock.patch.dict(sys.modules, {"code": mock_code}):
            cmd.python(options)

        self.assertEqual(
            mock_code.interact.mock_calls,
            [mock.call(local=cmd.get_namespace(**options))],
        )