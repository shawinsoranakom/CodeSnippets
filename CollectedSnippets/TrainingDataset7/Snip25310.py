def test_pointing_to_desc_field(self):
        class Model(models.Model):
            name = models.CharField(max_length=100)

            class Meta:
                indexes = [models.Index(fields=["-name"], name="index_name")]

        self.assertEqual(Model.check(databases=self.databases), [])