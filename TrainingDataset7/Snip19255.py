def test_cache_control_max_age(self):
        view = cache_page(2)(hello_world_view)
        request = self.factory.get("/view/")

        # First request. Freshly created response gets returned with no Age
        # header.
        with mock.patch.object(
            time, "time", return_value=1468749600
        ):  # Sun, 17 Jul 2016 10:00:00 GMT
            response = view(request, 1)
            response.close()
            self.assertIn("Expires", response)
            self.assertEqual(response["Expires"], "Sun, 17 Jul 2016 10:00:02 GMT")
            self.assertIn("Cache-Control", response)
            self.assertEqual(response["Cache-Control"], "max-age=2")
            self.assertNotIn("Age", response)

        # Second request one second later. Response from the cache gets
        # returned with an Age header set to 1 (second).
        with mock.patch.object(
            time, "time", return_value=1468749601
        ):  # Sun, 17 Jul 2016 10:00:01 GMT
            response = view(request, 1)
            response.close()
            self.assertIn("Expires", response)
            self.assertEqual(response["Expires"], "Sun, 17 Jul 2016 10:00:02 GMT")
            self.assertIn("Cache-Control", response)
            self.assertEqual(response["Cache-Control"], "max-age=2")
            self.assertIn("Age", response)
            self.assertEqual(response["Age"], "1")