def test_ticket_19102_defer(self):
        with self.assertNumQueries(1):
            Login.objects.filter(pk=self.l1.pk).filter(
                orgunit__name__isnull=False
            ).order_by("description").only("id").delete()
        self.assertFalse(Login.objects.filter(pk=self.l1.pk).exists())
        self.assertTrue(Login.objects.filter(pk=self.l2.pk).exists())