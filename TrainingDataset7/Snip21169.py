def test_ticket_19102_annotate(self):
        with self.assertNumQueries(1):
            Login.objects.order_by("description").filter(
                orgunit__name__isnull=False
            ).annotate(n=models.Count("description")).filter(
                n=1, pk=self.l1.pk
            ).delete()
        self.assertFalse(Login.objects.filter(pk=self.l1.pk).exists())
        self.assertTrue(Login.objects.filter(pk=self.l2.pk).exists())