def test_open_rating_route(self):
        for record_rating, is_rating_mixin_test in ((self.record_rating_thread, False),
                                                    (self.record_rating, True)):
            with self.subTest('With rating mixin' if is_rating_mixin_test else 'Without rating mixin'):
                """
                16.0 + expected behavior
                1) Clicking on the smiley image triggers the /rate/<string:token>/<int:rate>
                route should not update the rating of the record but simply redirect
                to the feedback form
                2) Customer interacts with webpage and submits FORM. Triggers /rate/<string:token>/submit_feedback
                route. Should update the rating of the record with the data in the POST request
                """
                self.authenticate(None, None)  # set up session for public user
                access_token = record_rating._rating_get_access_token()

                # First round of clicking the URL and then submitting FORM data
                response_click_one = self.url_open(f"/rate/{access_token}/5")
                response_click_one.raise_for_status()

                # there should be a form to post to validate the feedback and avoid one-click anyway
                forms = lxml.html.fromstring(response_click_one.content).xpath('//form')
                matching_rate_form = next((form for form in forms if form.get("action", "").startswith("/rate")), None)
                self.assertEqual(matching_rate_form.get('method'), 'post')
                self.assertEqual(matching_rate_form.get('action', ''), f'/rate/{access_token}/submit_feedback')

                # rating should not change, i.e. default values
                rating = record_rating.rating_ids
                self.assertFalse(rating.consumed)
                self.assertEqual(rating.rating, 0)
                self.assertFalse(rating.feedback)
                if is_rating_mixin_test:
                    self.assertEqual(record_rating.rating_last_value, 0)

                response_submit_one = self.url_open(
                    f"/rate/{access_token}/submit_feedback",
                    data={
                        "rate": 5,
                        "csrf_token": http.Request.csrf_token(self),
                        "feedback": "good",
                    }
                )
                response_submit_one.raise_for_status()

                rating_post_submit_one = record_rating.rating_ids
                self.assertTrue(rating_post_submit_one.consumed)
                self.assertEqual(rating_post_submit_one.rating, 5)
                self.assertEqual(rating_post_submit_one.feedback, "good")
                if is_rating_mixin_test:
                    self.assertEqual(record_rating.rating_last_value, 5)

                # Second round of clicking the URL and then submitting FORM data
                response_click_two = self.url_open(f"/rate/{access_token}/1")
                response_click_two.raise_for_status()
                if is_rating_mixin_test:
                    self.assertEqual(record_rating.rating_last_value, 5)  # should not be updated to 1

                # check returned form
                forms = lxml.html.fromstring(response_click_two.content).xpath('//form')
                matching_rate_form = next((form for form in forms if form.get("action", "").startswith("/rate")), None)
                self.assertEqual(matching_rate_form.get('method'), 'post')
                self.assertEqual(matching_rate_form.get('action', ''), f'/rate/{access_token}/submit_feedback')

                response_submit_two = self.url_open(
                    f"/rate/{access_token}/submit_feedback",
                    data={
                        "rate": 1,
                        "csrf_token": http.Request.csrf_token(self),
                        "feedback": "bad job"
                    }
                )
                response_submit_two.raise_for_status()

                rating_post_submit_second = record_rating.rating_ids
                self.assertTrue(rating_post_submit_second.consumed)
                self.assertEqual(rating_post_submit_second.rating, 1)
                self.assertEqual(rating_post_submit_second.feedback, "bad job")
                if is_rating_mixin_test:
                    self.assertEqual(record_rating.rating_last_value, 1)