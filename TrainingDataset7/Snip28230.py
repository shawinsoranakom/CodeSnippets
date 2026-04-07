def assertChoicesEqual(self, choices, objs):
        self.assertEqual(choices, [(obj.pk, str(obj)) for obj in objs])