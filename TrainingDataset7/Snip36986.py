def test_func():
                try:
                    raise RuntimeError("outer") from RuntimeError("inner")
                except RuntimeError as exc:
                    raise exc.__cause__