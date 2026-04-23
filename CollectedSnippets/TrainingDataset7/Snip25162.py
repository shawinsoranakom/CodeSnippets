def tearDown(self):
        gettext._translations = self.gettext_translations
        trans_real._translations = self.trans_real_translations