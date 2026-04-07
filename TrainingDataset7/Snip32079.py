def test_bpython(self):
        cmd = shell.Command()
        mock_bpython = mock.Mock(embed=mock.MagicMock())
        options = {"verbosity": 0, "no_imports": False}

        with mock.patch.dict(sys.modules, {"bpython": mock_bpython}):
            cmd.bpython(options)

        self.assertEqual(
            mock_bpython.embed.mock_calls, [mock.call(cmd.get_namespace(**options))]
        )