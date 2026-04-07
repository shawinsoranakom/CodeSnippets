def _test_range_overlaps(self, constraint):
        # Create exclusion constraint.
        self.assertNotIn(
            constraint.name, self.get_constraints(HotelReservation._meta.db_table)
        )
        with connection.schema_editor() as editor:
            editor.add_constraint(HotelReservation, constraint)
        self.assertIn(
            constraint.name, self.get_constraints(HotelReservation._meta.db_table)
        )
        # Add initial reservations.
        room101 = Room.objects.create(number=101)
        room102 = Room.objects.create(number=102)
        datetimes = [
            timezone.datetime(2018, 6, 20),
            timezone.datetime(2018, 6, 24),
            timezone.datetime(2018, 6, 26),
            timezone.datetime(2018, 6, 28),
            timezone.datetime(2018, 6, 29),
        ]
        reservation = HotelReservation.objects.create(
            datespan=DateRange(datetimes[0].date(), datetimes[1].date()),
            start=datetimes[0],
            end=datetimes[1],
            room=room102,
        )
        constraint.validate(HotelReservation, reservation)
        HotelReservation.objects.create(
            datespan=DateRange(datetimes[1].date(), datetimes[3].date()),
            start=datetimes[1],
            end=datetimes[3],
            room=room102,
        )
        HotelReservation.objects.create(
            datespan=DateRange(datetimes[3].date(), datetimes[4].date()),
            start=datetimes[3],
            end=datetimes[4],
            room=room102,
            cancelled=True,
        )
        # Overlap dates.
        with self.assertRaises(IntegrityError), transaction.atomic():
            reservation = HotelReservation(
                datespan=(datetimes[1].date(), datetimes[2].date()),
                start=datetimes[1],
                end=datetimes[2],
                room=room102,
            )
            msg = f"Constraint “{constraint.name}” is violated."
            with self.assertRaisesMessage(ValidationError, msg):
                constraint.validate(HotelReservation, reservation)
            reservation.save()
        # Valid range.
        other_valid_reservations = [
            # Other room.
            HotelReservation(
                datespan=(datetimes[1].date(), datetimes[2].date()),
                start=datetimes[1],
                end=datetimes[2],
                room=room101,
            ),
            # Cancelled reservation.
            HotelReservation(
                datespan=(datetimes[1].date(), datetimes[1].date()),
                start=datetimes[1],
                end=datetimes[2],
                room=room102,
                cancelled=True,
            ),
            # Other adjacent dates.
            HotelReservation(
                datespan=(datetimes[3].date(), datetimes[4].date()),
                start=datetimes[3],
                end=datetimes[4],
                room=room102,
            ),
        ]
        for reservation in other_valid_reservations:
            constraint.validate(HotelReservation, reservation)
        HotelReservation.objects.bulk_create(other_valid_reservations)
        # Excluded fields.
        constraint.validate(
            HotelReservation,
            HotelReservation(
                datespan=(datetimes[1].date(), datetimes[2].date()),
                start=datetimes[1],
                end=datetimes[2],
                room=room102,
            ),
            exclude={"room"},
        )
        constraint.validate(
            HotelReservation,
            HotelReservation(
                datespan=(datetimes[1].date(), datetimes[2].date()),
                start=datetimes[1],
                end=datetimes[2],
                room=room102,
            ),
            exclude={"datespan", "start", "end", "room"},
        )
        # Constraints with excluded fields in condition are ignored.
        constraint.validate(
            HotelReservation,
            HotelReservation(
                datespan=(datetimes[1].date(), datetimes[2].date()),
                start=datetimes[1],
                end=datetimes[2],
                room=room102,
            ),
            exclude={"cancelled"},
        )