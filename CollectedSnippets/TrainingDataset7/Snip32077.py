def test_ipython(self):
        cmd = shell.Command()
        mock_ipython = mock.Mock(start_ipython=mock.MagicMock())
        options = {"verbosity": 0, "no_imports": False}

        with mock.patch.dict(sys.modules, {"IPython": mock_ipython}):
            cmd.ipython(options)

        self.assertEqual(
            mock_ipython.start_ipython.mock_calls,
            [mock.call(argv=[], user_ns=cmd.get_namespace(**options))],
        )