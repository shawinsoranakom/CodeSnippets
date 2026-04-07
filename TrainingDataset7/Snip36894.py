def test_handle_db_exception(self):
        """
        Ensure the debug view works when a database exception is raised by
        performing an invalid query and passing the exception to the debug
        view.
        """
        with connection.cursor() as cursor:
            try:
                cursor.execute("INVALID SQL")
            except DatabaseError:
                exc_info = sys.exc_info()

        rf = RequestFactory()
        response = technical_500_response(rf.get("/"), *exc_info)
        self.assertContains(response, "OperationalError at /", status_code=500)