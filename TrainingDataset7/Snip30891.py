def test_ticket_23605(self):
        # Test filtering on a complicated q-object from ticket's report.
        # The query structure is such that we have multiple nested subqueries.
        # The original problem was that the inner queries weren't relabeled
        # correctly.
        # See also #24090.
        a1 = Ticket23605A.objects.create()
        a2 = Ticket23605A.objects.create()
        c1 = Ticket23605C.objects.create(field_c0=10000.0)
        Ticket23605B.objects.create(
            field_b0=10000.0, field_b1=True, modelc_fk=c1, modela_fk=a1
        )
        complex_q = Q(
            pk__in=Ticket23605A.objects.filter(
                Q(
                    # True for a1 as field_b0 = 10000, field_c0=10000
                    # False for a2 as no ticket23605b found
                    ticket23605b__field_b0__gte=1000000
                    / F("ticket23605b__modelc_fk__field_c0")
                )
                &
                # True for a1 (field_b1=True)
                Q(ticket23605b__field_b1=True)
                & ~Q(
                    ticket23605b__pk__in=Ticket23605B.objects.filter(
                        ~(
                            # Same filters as above commented filters, but
                            # double-negated (one for Q() above, one for
                            # parentheses). So, again a1 match, a2 not.
                            Q(field_b1=True)
                            & Q(field_b0__gte=1000000 / F("modelc_fk__field_c0"))
                        )
                    )
                )
            ).filter(ticket23605b__field_b1=True)
        )
        qs1 = Ticket23605A.objects.filter(complex_q)
        self.assertSequenceEqual(qs1, [a1])
        qs2 = Ticket23605A.objects.exclude(complex_q)
        self.assertSequenceEqual(qs2, [a2])