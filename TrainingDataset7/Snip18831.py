def test_unicode_password(self):
        old_password = connection.settings_dict["PASSWORD"]
        connection.settings_dict["PASSWORD"] = "françois"
        try:
            with connection.cursor():
                pass
        except DatabaseError:
            # As password is probably wrong, a database exception is expected
            pass
        except Exception as e:
            self.fail("Unexpected error raised with Unicode password: %s" % e)
        finally:
            connection.settings_dict["PASSWORD"] = old_password