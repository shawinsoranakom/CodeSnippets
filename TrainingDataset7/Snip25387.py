def test_db_table_comment_required_db_features(self):
        class Model(models.Model):
            class Meta:
                db_table_comment = "Table comment"
                required_db_features = {"supports_comments"}

        self.assertEqual(Model.check(databases=self.databases), [])