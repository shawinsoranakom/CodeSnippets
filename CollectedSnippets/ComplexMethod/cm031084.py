def test_buffer_overflow(self):
        # Older versions would have a buffer overflow when detecting
        # whether a link source was a directory. This test ensures we
        # no longer crash, but does not otherwise validate the behavior
        segment = 'X' * 27
        path = os.path.join(*[segment] * 10)
        test_cases = [
            # overflow with absolute src
            ('\\' + path, segment),
            # overflow dest with relative src
            (segment, path),
            # overflow when joining src
            (path[:180], path[:180]),
        ]
        for src, dest in test_cases:
            try:
                os.symlink(src, dest)
            except FileNotFoundError:
                pass
            else:
                try:
                    os.remove(dest)
                except OSError:
                    pass
            # Also test with bytes, since that is a separate code path.
            try:
                os.symlink(os.fsencode(src), os.fsencode(dest))
            except FileNotFoundError:
                pass
            else:
                try:
                    os.remove(dest)
                except OSError:
                    pass