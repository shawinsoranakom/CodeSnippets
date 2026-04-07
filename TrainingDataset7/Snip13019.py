def process_response(self, request, response):
        # Don't set it if it's already in the response
        if response.get("X-Frame-Options") is not None:
            return response

        # Don't set it if they used @xframe_options_exempt
        if getattr(response, "xframe_options_exempt", False):
            return response

        response.headers["X-Frame-Options"] = self.get_xframe_options_value(
            request,
            response,
        )
        return response