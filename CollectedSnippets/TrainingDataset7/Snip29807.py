def test_prepare_value(self):
        field = forms.HStoreField()
        self.assertEqual(
            field.prepare_value({"aira_maplayer": "Αρδευτικό δίκτυο"}),
            '{"aira_maplayer": "Αρδευτικό δίκτυο"}',
        )