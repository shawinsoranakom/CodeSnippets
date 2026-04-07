def test_dbms_session(self):
        """A stored procedure can be called through a cursor wrapper."""
        with connection.cursor() as cursor:
            cursor.callproc("DBMS_SESSION.SET_IDENTIFIER", ["_django_testing!"])