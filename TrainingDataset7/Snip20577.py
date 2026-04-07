def test_uuid4_unsupported(self):
        if connection.vendor == "mysql":
            if connection.mysql_is_mariadb:
                msg = "UUID4 requires MariaDB version 11.7 or later."
            else:
                msg = "UUID4 is not supported on MySQL."
        elif connection.vendor == "oracle":
            msg = "UUID4 requires Oracle version 23ai/26ai (23.9) or later."
        else:
            msg = "UUID4 is not supported on this database backend."

        with self.assertRaisesMessage(NotSupportedError, msg):
            UUIDModel.objects.update(uuid=UUID4())