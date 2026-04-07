def test_overridden_setup(self):
        class SetAttributeMixin:
            def setup(self, request, *args, **kwargs):
                self.attr = True
                super().setup(request, *args, **kwargs)

        class CheckSetupView(SetAttributeMixin, SimpleView):
            def dispatch(self, request, *args, **kwargs):
                assert hasattr(self, "attr")
                return super().dispatch(request, *args, **kwargs)

        response = CheckSetupView.as_view()(self.rf.get("/"))
        self.assertEqual(response.status_code, 200)