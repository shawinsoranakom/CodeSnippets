def test_issue_21554(self):
        senator = Senator.objects.create(name="John Doe", title="X", state="Y")
        senator = Senator.objects.get(pk=senator.pk)
        self.assertEqual(senator.name, "John Doe")
        self.assertEqual(senator.title, "X")
        self.assertEqual(senator.state, "Y")