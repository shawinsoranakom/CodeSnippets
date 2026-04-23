def test_ticket_24605(self):
        """
        Subquery table names should be quoted.
        """
        i1 = Individual.objects.create(alive=True)
        RelatedIndividual.objects.create(related=i1)
        i2 = Individual.objects.create(alive=False)
        RelatedIndividual.objects.create(related=i2)
        i3 = Individual.objects.create(alive=True)
        i4 = Individual.objects.create(alive=False)

        self.assertSequenceEqual(
            Individual.objects.filter(
                Q(alive=False), Q(related_individual__isnull=True)
            ),
            [i4],
        )
        self.assertSequenceEqual(
            Individual.objects.exclude(
                Q(alive=False), Q(related_individual__isnull=True)
            ).order_by("pk"),
            [i1, i2, i3],
        )