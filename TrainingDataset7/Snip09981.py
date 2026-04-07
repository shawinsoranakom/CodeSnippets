def supports_json_field(self):
        with self.connection.cursor() as cursor:
            try:
                with transaction.atomic(self.connection.alias):
                    cursor.execute('SELECT JSON(\'{"a": "b"}\')')
            except OperationalError:
                return False
        return True