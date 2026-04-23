def test_label_member(self):
        # label can be used as a member.
        Stationery = models.TextChoices("Stationery", "label stamp sticker")
        self.assertEqual(Stationery.label.label, "Label")
        self.assertEqual(Stationery.label.value, "label")
        self.assertEqual(Stationery.label.name, "label")