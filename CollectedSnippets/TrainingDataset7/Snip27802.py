def test_assignment_from_choice_enum(self):
        class Event(models.TextChoices):
            C = "Carnival!"
            F = "Festival!"

        p1 = Post.objects.create(title=Event.C, body=Event.F)
        p1.refresh_from_db()
        self.assertEqual(p1.title, "Carnival!")
        self.assertEqual(p1.body, "Festival!")
        self.assertEqual(p1.title, Event.C)
        self.assertEqual(p1.body, Event.F)
        p2 = Post.objects.get(title="Carnival!")
        self.assertEqual(p1, p2)
        self.assertEqual(p2.title, Event.C)