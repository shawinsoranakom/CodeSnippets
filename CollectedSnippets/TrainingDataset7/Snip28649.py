def test_name_auto_generation_with_quoted_db_table(self):
        class QuotedDbTable(models.Model):
            name = models.CharField(max_length=50)

            class Meta:
                db_table = '"t_quoted"'

        index = models.Index(fields=["name"])
        index.set_name_with_model(QuotedDbTable)
        self.assertEqual(index.name, "t_quoted_name_e4ed1b_idx")