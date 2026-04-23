def verify_unsafe_response(
        self, view, check_for_vars=True, check_for_POST_params=True
    ):
        """
        Asserts that potentially sensitive info are displayed in the response.
        """
        request = self.rf.post("/some_url/", self.breakfast_data)
        if iscoroutinefunction(view):
            response = async_to_sync(view)(request)
        else:
            response = view(request)
        if check_for_vars:
            # All variables are shown.
            self.assertContains(response, "cooked_eggs", status_code=500)
            self.assertContains(response, "scrambled", status_code=500)
            self.assertContains(response, "sauce", status_code=500)
            self.assertContains(response, "worcestershire", status_code=500)
        if check_for_POST_params:
            for k, v in self.breakfast_data.items():
                # All POST parameters are shown.
                self.assertContains(response, k, status_code=500)
                self.assertContains(response, v, status_code=500)