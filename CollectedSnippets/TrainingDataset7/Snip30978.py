def test_many_to_many(self):
        """
        Test of a simple raw query against a model containing a m2m field
        """
        query = "SELECT * FROM raw_query_reviewer"
        reviewers = Reviewer.objects.all()
        self.assertSuccessfulRawQuery(Reviewer, query, reviewers)