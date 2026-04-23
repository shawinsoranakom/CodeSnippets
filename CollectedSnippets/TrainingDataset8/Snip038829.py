def test_uncaught_app_exception(self):
        err = None
        try:
            st.format("http://not_an_image.png", width=-1)
        except Exception as e:
            err = UncaughtAppException(e)
        self.assertIsNotNone(err)

        # Marshall it.
        proto = ExceptionProto()
        exception.marshall(proto, err)

        for line in proto.stack_trace:
            # assert message that could contain secret information in the stack trace
            assert "module 'streamlit' has no attribute 'format'" not in line

        assert proto.message == _GENERIC_UNCAUGHT_EXCEPTION_TEXT
        assert proto.type == "AttributeError"