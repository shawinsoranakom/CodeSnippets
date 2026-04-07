def test_foreign_key_db_on_delete(self):
        out = StringIO()
        call_command("inspectdb", "inspectdb_dbondeletemodel", stdout=out)
        output = out.getvalue()
        self.assertIn(
            "fk_do_nothing = models.ForeignKey('InspectdbUniquetogether', "
            "models.DO_NOTHING)",
            output,
        )
        self.assertIn(
            "fk_db_cascade = models.ForeignKey('InspectdbColumntypes', "
            "models.DB_CASCADE)",
            output,
        )
        self.assertIn(
            "fk_set_null = models.ForeignKey('InspectdbDigitsincolumnname', "
            "models.DB_SET_NULL, blank=True, null=True)",
            output,
        )