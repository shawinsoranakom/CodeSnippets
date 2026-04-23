def test_dict_behavior(self):
        """
        Test for bug #14020: Make HttpResponse.get work like dict.get
        """
        r = HttpResponse()
        self.assertIsNone(r.get("test"))