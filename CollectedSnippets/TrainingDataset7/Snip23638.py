def test_not_calling_parent_setup_error(self):
        class TestView(View):
            def setup(self, request, *args, **kwargs):
                pass  # Not calling super().setup()

        msg = (
            "TestView instance has no 'request' attribute. Did you override "
            "setup() and forget to call super()?"
        )
        with self.assertRaisesMessage(AttributeError, msg):
            TestView.as_view()(self.rf.get("/"))