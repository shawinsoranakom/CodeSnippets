def test_or_with_both_slice_and_ordering(self):
        qs1 = Classroom.objects.filter(has_blackboard=False).order_by("-pk")[:1]
        qs2 = Classroom.objects.filter(has_blackboard=True).order_by("-name")[:1]
        self.assertCountEqual(qs1 | qs2, [self.room_3, self.room_4])