def test_enums(self):
        for name in dir(signal):
            sig = getattr(signal, name)
            if name in {'SIG_DFL', 'SIG_IGN'}:
                self.assertIsInstance(sig, signal.Handlers)
            elif name in {'SIG_BLOCK', 'SIG_UNBLOCK', 'SIG_SETMASK'}:
                self.assertIsInstance(sig, signal.Sigmasks)
            elif name.startswith('SIG') and not name.startswith('SIG_'):
                self.assertIsInstance(sig, signal.Signals)
            elif name.startswith('CTRL_'):
                self.assertIsInstance(sig, signal.Signals)
                self.assertEqual(sys.platform, "win32")

        CheckedSignals = enum._old_convert_(
                enum.IntEnum, 'Signals', 'signal',
                lambda name:
                    name.isupper()
                    and (name.startswith('SIG') and not name.startswith('SIG_'))
                    or name.startswith('CTRL_'),
                source=signal,
                )
        enum._test_simple_enum(CheckedSignals, signal.Signals)

        CheckedHandlers = enum._old_convert_(
                enum.IntEnum, 'Handlers', 'signal',
                lambda name: name in ('SIG_DFL', 'SIG_IGN'),
                source=signal,
                )
        enum._test_simple_enum(CheckedHandlers, signal.Handlers)

        Sigmasks = getattr(signal, 'Sigmasks', None)
        if Sigmasks is not None:
            CheckedSigmasks = enum._old_convert_(
                    enum.IntEnum, 'Sigmasks', 'signal',
                    lambda name: name in ('SIG_BLOCK', 'SIG_UNBLOCK', 'SIG_SETMASK'),
                    source=signal,
                    )
            enum._test_simple_enum(CheckedSigmasks, Sigmasks)