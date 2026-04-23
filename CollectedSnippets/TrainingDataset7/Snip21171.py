def test_ticket_19102_select_related(self):
        with self.assertNumQueries(1):
            Login.objects.filter(pk=self.l1.pk).filter(
                orgunit__name__isnull=False
            ).order_by("description").select_related("orgunit").delete()
        self.assertFalse(Login.objects.filter(pk=self.l1.pk).exists())
        self.assertTrue(Login.objects.filter(pk=self.l2.pk).exists())