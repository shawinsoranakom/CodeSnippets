def test_issue_11764(self):
        """
        Regression test for #11764
        """
        wholesalers = list(Wholesaler.objects.select_related())
        self.assertEqual(wholesalers, [])