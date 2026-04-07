def test_recursive_m2m_all(self):
        for person, colleagues in (
            (self.a, [self.b, self.c, self.d]),
            (self.b, [self.a]),
            (self.c, [self.a, self.d]),
            (self.d, [self.a, self.c]),
        ):
            with self.subTest(person=person):
                self.assertSequenceEqual(person.colleagues.all(), colleagues)