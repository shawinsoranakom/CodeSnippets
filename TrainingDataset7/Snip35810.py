def test_no_illegal_imports(self):
        # modules that are not listed in urlpatterns should not be importable
        redirect("urlpatterns_reverse.nonimported_module.view")
        self.assertNotIn("urlpatterns_reverse.nonimported_module", sys.modules)