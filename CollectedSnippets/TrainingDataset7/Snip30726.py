def test_or_with_both_slice(self):
        qs1 = Classroom.objects.filter(has_blackboard=False)[:1]
        qs2 = Classroom.objects.filter(has_blackboard=True)[:1]
        self.assertCountEqual(qs1 | qs2, [self.room_1, self.room_2])