def test_text_attribute_error(self):
        r = StreamingHttpResponse(iter(["hello", "world"]))
        msg = "This %s instance has no `text` attribute." % r.__class__.__name__

        with self.assertRaisesMessage(AttributeError, msg):
            r.text