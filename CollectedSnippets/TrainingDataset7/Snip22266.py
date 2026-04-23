def test_nk_on_serialize(self):
        """
        Natural key requirements are taken into account when serializing
        models.
        """
        management.call_command(
            "loaddata",
            "forward_ref_lookup.json",
            verbosity=0,
        )

        out = StringIO()
        management.call_command(
            "dumpdata",
            "fixtures_regress.book",
            "fixtures_regress.person",
            "fixtures_regress.store",
            verbosity=0,
            format="json",
            use_natural_foreign_keys=True,
            use_natural_primary_keys=True,
            stdout=out,
        )
        self.assertJSONEqual(
            out.getvalue(),
            """
            [{"fields": {"main": null, "name": "Amazon"},
            "model": "fixtures_regress.store"},
            {"fields": {"main": null, "name": "Borders"},
            "model": "fixtures_regress.store"},
            {"fields": {"name": "Neal Stephenson"}, "model": "fixtures_regress.person"},
            {"pk": 1, "model": "fixtures_regress.book",
            "fields": {"stores": [["Amazon"], ["Borders"]],
            "name": "Cryptonomicon", "author": ["Neal Stephenson"]}}]
            """,
        )