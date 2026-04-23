def _real_bulk_solve(self, /, requests: list[JsChallengeRequest]):
        grouped: dict[str, list[JsChallengeRequest]] = collections.defaultdict(list)
        for request in requests:
            grouped[request.input.player_url].append(request)

        for player_url, grouped_requests in grouped.items():
            player = None
            if self._ENABLE_PREPROCESSED_PLAYER_CACHE:
                player = self.ie.cache.load(self._CACHE_SECTION, f'player:{player_url}')

            if player:
                cached = True
            else:
                cached = False
                video_id = next((request.video_id for request in grouped_requests), None)
                player = self._get_player(video_id, player_url)

            # NB: This output belongs after the player request
            self.logger.info(f'Solving JS challenges using {self.JS_RUNTIME_NAME}')

            stdin = self._construct_stdin(player, cached, grouped_requests)
            stdout = self._run_js_runtime(stdin)
            output = json.loads(stdout)
            if output['type'] == 'error':
                raise JsChallengeProviderError(output['error'])

            if self._ENABLE_PREPROCESSED_PLAYER_CACHE and (preprocessed := output.get('preprocessed_player')):
                self.ie.cache.store(self._CACHE_SECTION, f'player:{player_url}', preprocessed)

            for request, response_data in zip(grouped_requests, output['responses'], strict=True):
                if response_data['type'] == 'error':
                    yield JsChallengeProviderResponse(request, None, response_data['error'])
                else:
                    yield JsChallengeProviderResponse(request, JsChallengeResponse(request.type, (
                        NChallengeOutput(response_data['data']) if request.type is JsChallengeType.N
                        else SigChallengeOutput(response_data['data']))))