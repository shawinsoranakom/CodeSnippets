def test_mti_update_parent_through_child(self):
        Politician.objects.create()
        Congressman.objects.create()
        Congressman.objects.update(title="senator 1")
        self.assertEqual(Congressman.objects.get().title, "senator 1")