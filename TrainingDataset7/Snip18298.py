def assertFormError(self, response, error):
        """Assert that error is found in response.context['form'] errors"""
        form_errors = list(itertools.chain(*response.context["form"].errors.values()))
        self.assertIn(str(error), form_errors)