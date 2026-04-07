def test_same_relations(self):
        out = StringIO()
        call_command("inspectdb", "inspectdb_message", stdout=out)
        self.assertIn(
            "author = models.ForeignKey('InspectdbPeople', models.DO_NOTHING, "
            "related_name='inspectdbmessage_author_set')",
            out.getvalue(),
        )