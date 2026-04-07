def test_server_side_cursor(self):
        self.assertUsesCursor(Person.objects.iterator())