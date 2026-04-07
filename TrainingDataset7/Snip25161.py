def setUp(self):
        self.gettext_translations = gettext_module._translations.copy()
        self.trans_real_translations = trans_real._translations.copy()