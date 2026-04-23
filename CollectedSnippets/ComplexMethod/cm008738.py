def bulk_solve(self, requests: list[JsChallengeRequest]) -> list[tuple[JsChallengeRequest, JsChallengeResponse]]:
        """Solves multiple JS Challenges in bulk, returning a list of responses"""
        if not self.providers:
            self.logger.trace('No JS Challenge providers registered')
            return []

        results = []
        next_requests = requests[:]

        skipped_components = []
        for provider in self._get_providers(next_requests):
            if not next_requests:
                break
            self.logger.trace(
                f'Attempting to solve {len(next_requests)} challenges using "{provider.PROVIDER_NAME}" provider')
            try:
                for response in provider.bulk_solve([dataclasses.replace(request) for request in next_requests]):
                    if not validate_provider_response(response):
                        self.logger.warning(
                            f'JS Challenge Provider "{provider.PROVIDER_NAME}" returned an invalid response:'
                            f'         response = {response!r}\n'
                            f'         {provider_bug_report_message(provider, before="")}')
                        continue
                    if response.error:
                        self._handle_error(response.error, provider, [response.request])
                        continue
                    if (vr_msg := validate_response(response.response, response.request)) is not True:
                        self.logger.warning(
                            f'Invalid JS Challenge response received from "{provider.PROVIDER_NAME}" provider: {vr_msg or ""}\n'
                            f'         response = {response.response}\n'
                            f'         request = {response.request}\n'
                            f'         {provider_bug_report_message(provider, before="")}')
                        continue
                    try:
                        next_requests.remove(response.request)
                    except ValueError:
                        self.logger.warning(
                            f'JS Challenge Provider "{provider.PROVIDER_NAME}" returned a response for an unknown request:\n'
                            f'         request = {response.request}\n'
                            f'         {provider_bug_report_message(provider, before="")}')
                        continue
                    results.append((response.request, response.response))
            except Exception as e:
                if isinstance(e, JsChallengeProviderRejectedRequest) and e._skipped_components:
                    skipped_components.extend(e._skipped_components)
                self._handle_error(e, provider, next_requests)
                continue

        if skipped_components:
            self.__report_skipped_components(skipped_components)

        if len(results) != len(requests):
            self.logger.trace(
                f'Not all JS Challenges were solved, expected {len(requests)} responses, got {len(results)}')
            self.logger.trace(f'Unsolved requests: {next_requests}')
        else:
            self.logger.trace(f'Solved all {len(requests)} requested JS Challenges')
        return results