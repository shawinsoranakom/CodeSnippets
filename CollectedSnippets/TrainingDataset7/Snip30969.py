def test_db_column_handler(self):
        """
        Test of a simple raw query against a model containing a field with
        db_column defined.
        """
        query = "SELECT * FROM raw_query_coffee"
        coffees = Coffee.objects.all()
        self.assertSuccessfulRawQuery(Coffee, query, coffees)