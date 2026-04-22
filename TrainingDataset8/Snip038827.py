def test_markdown_flag(self):
        """Test that ExceptionProtos for StreamlitAPIExceptions (and
        subclasses) have the "message_is_markdown" flag set.
        """
        proto = ExceptionProto()
        exception.marshall(proto, RuntimeError("oh no!"))
        self.assertFalse(proto.message_is_markdown)

        proto = ExceptionProto()
        exception.marshall(proto, StreamlitAPIException("oh no!"))
        self.assertTrue(proto.message_is_markdown)

        proto = ExceptionProto()
        exception.marshall(proto, errors.DuplicateWidgetID("oh no!"))
        self.assertTrue(proto.message_is_markdown)