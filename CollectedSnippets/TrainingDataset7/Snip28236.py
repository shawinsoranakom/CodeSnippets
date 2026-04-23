def assertChoicesEqual(self, choices, objs):
        self.assertCountEqual(choices, [(obj.pk, str(obj)) for obj in objs])