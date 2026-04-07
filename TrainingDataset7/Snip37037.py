def test_i18n_unknown_package_error(self):
        view = JavaScriptCatalog.as_view()
        request = RequestFactory().get("/")
        msg = "Invalid package(s) provided to JavaScriptCatalog: unknown_package"
        with self.assertRaisesMessage(ValueError, msg):
            view(request, packages="unknown_package")
        msg += ",unknown_package2"
        with self.assertRaisesMessage(ValueError, msg):
            view(request, packages="unknown_package+unknown_package2")