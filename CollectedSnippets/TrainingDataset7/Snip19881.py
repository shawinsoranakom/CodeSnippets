def test_content_type_db_on_delete(self):
        class Model(models.Model):
            content_type = models.ForeignKey(ContentType, models.DB_CASCADE)
            object_id = models.PositiveIntegerField()
            content_object = GenericForeignKey("content_type", "object_id")

        field = Model._meta.get_field("content_object")

        self.assertEqual(
            field.check(),
            [
                checks.Error(
                    "'Model.content_type' cannot use the database-level on_delete "
                    "variant.",
                    hint="Change the on_delete rule to the non-database variant.",
                    obj=field,
                    id="contenttypes.E006",
                )
            ],
        )