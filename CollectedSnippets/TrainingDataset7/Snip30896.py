def test_ticket_23622(self):
        """
        Make sure __pk__in and __in work the same for related fields when
        using a distinct on subquery.
        """
        a1 = Ticket23605A.objects.create()
        a2 = Ticket23605A.objects.create()
        c1 = Ticket23605C.objects.create(field_c0=0.0)
        Ticket23605B.objects.create(
            modela_fk=a1,
            field_b0=123,
            field_b1=True,
            modelc_fk=c1,
        )
        Ticket23605B.objects.create(
            modela_fk=a1,
            field_b0=23,
            field_b1=True,
            modelc_fk=c1,
        )
        Ticket23605B.objects.create(
            modela_fk=a1,
            field_b0=234,
            field_b1=True,
            modelc_fk=c1,
        )
        Ticket23605B.objects.create(
            modela_fk=a1,
            field_b0=12,
            field_b1=True,
            modelc_fk=c1,
        )
        Ticket23605B.objects.create(
            modela_fk=a2,
            field_b0=567,
            field_b1=True,
            modelc_fk=c1,
        )
        Ticket23605B.objects.create(
            modela_fk=a2,
            field_b0=76,
            field_b1=True,
            modelc_fk=c1,
        )
        Ticket23605B.objects.create(
            modela_fk=a2,
            field_b0=7,
            field_b1=True,
            modelc_fk=c1,
        )
        Ticket23605B.objects.create(
            modela_fk=a2,
            field_b0=56,
            field_b1=True,
            modelc_fk=c1,
        )
        qx = Q(
            ticket23605b__pk__in=Ticket23605B.objects.order_by(
                "modela_fk", "-field_b1"
            ).distinct("modela_fk")
        ) & Q(ticket23605b__field_b0__gte=300)
        qy = Q(
            ticket23605b__in=Ticket23605B.objects.order_by(
                "modela_fk", "-field_b1"
            ).distinct("modela_fk")
        ) & Q(ticket23605b__field_b0__gte=300)
        self.assertEqual(
            set(Ticket23605A.objects.filter(qx).values_list("pk", flat=True)),
            set(Ticket23605A.objects.filter(qy).values_list("pk", flat=True)),
        )
        self.assertSequenceEqual(Ticket23605A.objects.filter(qx), [a2])