def test_xor_with_lhs_slice(self):
        qs1 = Classroom.objects.filter(has_blackboard=True)[:1]
        qs2 = Classroom.objects.filter(has_blackboard=False)
        self.assertCountEqual(qs1 ^ qs2, [self.room_1, self.room_2, self.room_4])