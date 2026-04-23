def _get_template_used(self, response, template_name, msg_prefix, method_name):
        if response is None and template_name is None:
            raise TypeError("response and/or template_name argument must be provided")

        if msg_prefix:
            msg_prefix += ": "

        if template_name is not None and response is not None:
            self._check_test_client_response(response, "templates", method_name)

        if not hasattr(response, "templates") or (response is None and template_name):
            if response:
                template_name = response
                response = None
            # use this template with context manager
            return template_name, None, msg_prefix

        template_names = [t.name for t in response.templates if t.name is not None]
        return None, template_names, msg_prefix