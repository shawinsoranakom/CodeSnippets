def test_ticket_19102_extra(self):
        with self.assertNumQueries(1):
            Login.objects.order_by("description").filter(
                orgunit__name__isnull=False
            ).extra(select={"extraf": "1"}).filter(pk=self.l1.pk).delete()
        self.assertFalse(Login.objects.filter(pk=self.l1.pk).exists())
        self.assertTrue(Login.objects.filter(pk=self.l2.pk).exists())