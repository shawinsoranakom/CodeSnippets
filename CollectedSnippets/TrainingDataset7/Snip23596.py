def test_ticket_22998(self):
        related = Related.objects.create()
        content = Content.objects.create(related_obj=related)
        Node.objects.create(content=content)

        # deleting the Related cascades to the Content cascades to the Node,
        # where the pre_delete signal should fire and prevent deletion.
        with self.assertRaises(ProtectedError):
            related.delete()