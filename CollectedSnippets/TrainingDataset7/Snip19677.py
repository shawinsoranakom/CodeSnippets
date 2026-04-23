def test_update_or_create_with_pre_save_pk_field(self):
        t = TimeStamped.objects.create(id=1)
        self.assertEqual(TimeStamped.objects.count(), 1)
        t, created = TimeStamped.objects.update_or_create(
            pk=t.pk, defaults={"text": "new text"}
        )
        self.assertIs(created, False)
        self.assertEqual(TimeStamped.objects.count(), 1)
        self.assertEqual(t.text, "new text")