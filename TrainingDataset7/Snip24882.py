def test_verbose_name(self):
        company_type = ContentType.objects.get(app_label="i18n", model="company")
        with translation.override("en"):
            self.assertEqual(str(company_type), "I18N | Company")
        with translation.override("fr"):
            self.assertEqual(str(company_type), "I18N | Société")