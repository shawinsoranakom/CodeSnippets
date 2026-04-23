def test_max_batch_size(self):
        max_batch_size = connection.ops.bulk_batch_size(
            # PK is used twice, see comment in bulk_update().
            [Note._meta.pk, Note._meta.pk, Note._meta.get_field("note")],
            self.notes,
        )
        with self.assertNumQueries(ceil(len(self.notes) / max_batch_size)):
            Note.objects.bulk_update(self.notes, fields=["note"])