def test_mti_update_grand_parent_through_child(self):
        Politician.objects.create()
        Senator.objects.create()
        Senator.objects.update(title="senator 1")
        self.assertEqual(Senator.objects.get().title, "senator 1")