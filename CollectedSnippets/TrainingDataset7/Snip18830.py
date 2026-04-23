def test_unicode_fetches(self):
        # fetchone, fetchmany, fetchall return strings as Unicode objects.
        qn = connection.ops.quote_name
        Person(first_name="John", last_name="Doe").save()
        Person(first_name="Jane", last_name="Doe").save()
        Person(first_name="Mary", last_name="Agnelline").save()
        Person(first_name="Peter", last_name="Parker").save()
        Person(first_name="Clark", last_name="Kent").save()
        opts2 = Person._meta
        f3, f4 = opts2.get_field("first_name"), opts2.get_field("last_name")
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT %s, %s FROM %s ORDER BY %s"
                % (
                    qn(f3.column),
                    qn(f4.column),
                    connection.introspection.identifier_converter(opts2.db_table),
                    qn(f3.column),
                )
            )
            self.assertEqual(cursor.fetchone(), ("Clark", "Kent"))
            self.assertEqual(
                list(cursor.fetchmany(2)), [("Jane", "Doe"), ("John", "Doe")]
            )
            self.assertEqual(
                list(cursor.fetchall()), [("Mary", "Agnelline"), ("Peter", "Parker")]
            )