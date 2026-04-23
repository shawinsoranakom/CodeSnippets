def send(self, request: Request) -> Response:
        """
        Passes a request onto a suitable RequestHandler
        """
        if not self.handlers:
            raise RequestError('No request handlers configured')

        assert isinstance(request, Request)

        unexpected_errors = []
        unsupported_errors = []
        for handler in self._get_handlers(request):
            self._print_verbose(f'Checking if "{handler.RH_NAME}" supports this request.')
            try:
                handler.validate(request)
            except UnsupportedRequest as e:
                self._print_verbose(
                    f'"{handler.RH_NAME}" cannot handle this request (reason: {error_to_str(e)})')
                unsupported_errors.append(e)
                continue

            self._print_verbose(f'Sending request via "{handler.RH_NAME}"')
            try:
                response = handler.send(request)
            except RequestError:
                raise
            except Exception as e:
                self.logger.error(
                    f'[{handler.RH_NAME}] Unexpected error: {error_to_str(e)}{bug_reports_message()}',
                    is_error=False)
                unexpected_errors.append(e)
                continue

            assert isinstance(response, Response)
            return response

        raise NoSupportingHandlers(unsupported_errors, unexpected_errors)