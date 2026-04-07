def test_database_routing(self):
        note = Note.objects.create(note="create")
        note.note = "bulk_update"
        with self.assertNumQueries(1, using="other"):
            Note.objects.bulk_update([note], fields=["note"])