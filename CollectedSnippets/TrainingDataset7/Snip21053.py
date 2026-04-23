def test_ticket_16409(self):
        # Regression for #16409 - make sure defer() and only() work with
        # annotate()
        self.assertIsInstance(
            list(SimpleItem.objects.annotate(Count("feature")).defer("name")), list
        )
        self.assertIsInstance(
            list(SimpleItem.objects.annotate(Count("feature")).only("name")), list
        )