def _assert_mail_attachments_widget(self, wizard, expected_values_list):
        self.assertEqual(len(wizard.mail_attachments_widget), len(expected_values_list))
        for values, expected_values in zip(wizard.mail_attachments_widget, expected_values_list):
            try:
                int(values['id'])
                check_id_needed = True
            except ValueError:
                check_id_needed = False
            self.assertDictEqual(
                {k: v for k, v in values.items() if not check_id_needed and k != 'id'},
                {k: v for k, v in expected_values.items() if not check_id_needed and k != 'id'},
            )