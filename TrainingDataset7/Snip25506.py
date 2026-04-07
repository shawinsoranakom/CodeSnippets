def test_db_comment_required_db_features(self):
        class Model(models.Model):
            field = models.IntegerField(db_comment="Column comment")

            class Meta:
                required_db_features = {"supports_comments"}

        errors = Model._meta.get_field("field").check(databases=self.databases)
        self.assertEqual(errors, [])