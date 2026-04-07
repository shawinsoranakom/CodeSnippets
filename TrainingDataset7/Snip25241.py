def test_foreign_key_to_field(self):
        out = StringIO()
        call_command("inspectdb", "inspectdb_foreignkeytofield", stdout=out)
        self.assertIn(
            "to_field_fk = models.ForeignKey('InspectdbPeoplemoredata', "
            "models.DO_NOTHING, to_field='people_unique_id')",
            out.getvalue(),
        )