def test_detail_object_does_not_exist(self):
        with self.assertRaises(ObjectDoesNotExist):
            self.client.get("/detail/doesnotexist/1/")