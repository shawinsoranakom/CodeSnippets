def test_sequence_creation(self):
        """
        Sequences on an m2m_through are created for the through model, not a
        phantom auto-generated m2m table (#11107).
        """
        out = StringIO()
        management.call_command(
            "dumpdata", "m2m_through_regress", format="json", stdout=out
        )
        self.assertJSONEqual(
            out.getvalue().strip(),
            '[{"pk": 1, "model": "m2m_through_regress.usermembership", '
            '"fields": {"price": 100, "group": 1, "user": 1}}, '
            '{"pk": 1, "model": "m2m_through_regress.person", '
            '"fields": {"name": "Guido"}}, '
            '{"pk": 1, "model": "m2m_through_regress.group", '
            '"fields": {"name": "Python Core Group"}}]',
        )