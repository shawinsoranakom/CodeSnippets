def test_closed_server_side_cursor(self):
        persons = Person.objects.iterator()
        next(persons)  # Open a server-side cursor
        del persons
        garbage_collect()
        cursors = self.inspect_cursors()
        self.assertEqual(len(cursors), 0)