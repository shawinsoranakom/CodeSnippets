def test_or_with_rhs_slice(self):
        qs1 = Classroom.objects.filter(has_blackboard=True)
        qs2 = Classroom.objects.filter(has_blackboard=False)[:1]
        self.assertCountEqual(qs1 | qs2, [self.room_1, self.room_2, self.room_3])