def test_aggregate(self):
        """
        filtered_relation() not only improves performance but also creates
        correct results when aggregating with multiple LEFT JOINs.

        Books can be reserved then rented by a borrower. Each reservation and
        rental session are recorded with Reservation and RentalSession models.
        Every time a reservation or a rental session is over, their state is
        changed to 'stopped'.

        Goal: Count number of books that are either currently reserved or
        rented by borrower1 or available.
        """
        qs = (
            Book.objects.annotate(
                is_reserved_or_rented_by=Case(
                    When(
                        reservation__state=Reservation.NEW,
                        then=F("reservation__borrower__pk"),
                    ),
                    When(
                        rental_session__state=RentalSession.NEW,
                        then=F("rental_session__borrower__pk"),
                    ),
                    default=None,
                )
            )
            .filter(
                Q(is_reserved_or_rented_by=self.borrower1.pk) | Q(state=Book.AVAILABLE)
            )
            .distinct()
        )
        self.assertEqual(qs.count(), 1)
        # If count is equal to 1, the same aggregation should return in the
        # same result but it returns 4.
        self.assertSequenceEqual(
            qs.annotate(total=Count("pk")).values("total"), [{"total": 4}]
        )
        # With FilteredRelation, the result is as expected (1).
        qs = (
            Book.objects.annotate(
                active_reservations=FilteredRelation(
                    "reservation",
                    condition=Q(
                        reservation__state=Reservation.NEW,
                        reservation__borrower=self.borrower1,
                    ),
                ),
            )
            .annotate(
                active_rental_sessions=FilteredRelation(
                    "rental_session",
                    condition=Q(
                        rental_session__state=RentalSession.NEW,
                        rental_session__borrower=self.borrower1,
                    ),
                ),
            )
            .filter(
                (
                    Q(active_reservations__isnull=False)
                    | Q(active_rental_sessions__isnull=False)
                )
                | Q(state=Book.AVAILABLE)
            )
            .distinct()
        )
        self.assertEqual(qs.count(), 1)
        self.assertSequenceEqual(
            qs.annotate(total=Count("pk")).values("total"), [{"total": 1}]
        )