def test_jsonb_agg_key_index_transforms(self):
        room101 = Room.objects.create(number=101)
        room102 = Room.objects.create(number=102)
        datetimes = [
            timezone.datetime(2018, 6, 20),
            timezone.datetime(2018, 6, 24),
            timezone.datetime(2018, 6, 28),
        ]
        HotelReservation.objects.create(
            datespan=(datetimes[0].date(), datetimes[1].date()),
            start=datetimes[0],
            end=datetimes[1],
            room=room102,
            requirements={"double_bed": True, "parking": True},
        )
        HotelReservation.objects.create(
            datespan=(datetimes[1].date(), datetimes[2].date()),
            start=datetimes[1],
            end=datetimes[2],
            room=room102,
            requirements={"double_bed": False, "sea_view": True, "parking": False},
        )
        HotelReservation.objects.create(
            datespan=(datetimes[0].date(), datetimes[2].date()),
            start=datetimes[0],
            end=datetimes[2],
            room=room101,
            requirements={"sea_view": False},
        )
        values = (
            Room.objects.annotate(
                requirements=JSONBAgg(
                    "hotelreservation__requirements",
                    order_by="-hotelreservation__start",
                )
            )
            .filter(requirements__0__sea_view=True)
            .values("number", "requirements")
        )
        self.assertSequenceEqual(
            values,
            [
                {
                    "number": 102,
                    "requirements": [
                        {"double_bed": False, "sea_view": True, "parking": False},
                        {"double_bed": True, "parking": True},
                    ],
                },
            ],
        )