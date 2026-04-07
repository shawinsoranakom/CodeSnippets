def update_birthday_slowly():
            Person.objects.update_or_create(
                first_name="John", defaults={"birthday": birthday_sleep}
            )
            # Avoid leaking connection for Oracle
            connection.close()