def tearDown(self):
        gettext_module.find = self.gettext_find_builtin
        super().tearDown()