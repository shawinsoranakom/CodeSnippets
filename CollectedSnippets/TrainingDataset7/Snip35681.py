def test_update_fields_expression(self):
        obj = Person.objects.create(name="Valerie", gender="F", pid=42)
        updated_pid = F("pid") + 1
        obj.pid = updated_pid
        obj.save(update_fields={"gender"})
        self.assertIs(obj.pid, updated_pid)
        obj.save(update_fields={"pid"})
        expected_num_queries = (
            0 if connection.features.can_return_rows_from_update else 1
        )
        with self.assertNumQueries(expected_num_queries):
            self.assertEqual(obj.pid, 43)