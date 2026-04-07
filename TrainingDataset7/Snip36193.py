def setUp(self):
        self.dict1 = CaseInsensitiveMapping(
            {
                "Accept": "application/json",
                "content-type": "text/html",
            }
        )