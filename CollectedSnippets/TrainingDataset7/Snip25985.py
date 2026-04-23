def test_order_by_relational_field_through_model(self):
        today = datetime.now()
        yesterday = today - timedelta(days=1)
        CustomMembership.objects.create(
            person=self.jim, group=self.rock, date_joined=yesterday
        )
        CustomMembership.objects.create(
            person=self.bob, group=self.rock, date_joined=today
        )
        CustomMembership.objects.create(
            person=self.jane, group=self.roll, date_joined=yesterday
        )
        CustomMembership.objects.create(
            person=self.jim, group=self.roll, date_joined=today
        )
        self.assertSequenceEqual(
            self.rock.custom_members.order_by("custom_person_related_name"),
            [self.jim, self.bob],
        )
        self.assertSequenceEqual(
            self.roll.custom_members.order_by("custom_person_related_name"),
            [self.jane, self.jim],
        )