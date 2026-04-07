def test_unsaved_models(self):
        objs = self.notes + [Note(note="test", misc="test")]
        msg = "All bulk_update() objects must have a primary key set."
        with self.assertRaisesMessage(ValueError, msg):
            Note.objects.bulk_update(objs, fields=["note"])