def update_person():
            try:
                with patch.object(Person, "save", wait_for_allowed_save):
                    Person.objects.update_or_create(
                        first_name="John",
                        defaults={"last_name": "Doe", "birthday": birthday_yield},
                    )
            finally:
                # Avoid leaking connection for Oracle.
                connection.close()