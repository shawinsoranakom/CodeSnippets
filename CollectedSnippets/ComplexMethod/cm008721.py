def solve_js_challenges():
            # Solve all n/sig challenges in bulk and store the results in self._player_cache
            challenge_requests = []
            if n_challenges:
                challenge_requests.append(JsChallengeRequest(
                    type=JsChallengeType.N,
                    video_id=video_id,
                    input=NChallengeInput(challenges=list(n_challenges), player_url=player_url)))
            if s_challenges:
                cached_sigfuncs = set()
                for spec_id in s_challenges:
                    if self._load_player_data_from_cache('sigfuncs', player_url, spec_id, use_disk_cache=True):
                        cached_sigfuncs.add(spec_id)
                s_challenges.difference_update(cached_sigfuncs)

                challenge_requests.append(JsChallengeRequest(
                    type=JsChallengeType.SIG,
                    video_id=video_id,
                    input=SigChallengeInput(
                        challenges=[''.join(map(chr, range(spec_id))) for spec_id in s_challenges],
                        player_url=player_url)))

            if challenge_requests:
                for _challenge_request, challenge_response in self._jsc_director.bulk_solve(challenge_requests):
                    if challenge_response.type == JsChallengeType.SIG:
                        for challenge, result in challenge_response.output.results.items():
                            spec_id = len(challenge)
                            self._store_player_data_to_cache(
                                [ord(c) for c in result], 'sigfuncs',
                                player_url, spec_id, use_disk_cache=True)
                            if spec_id in s_challenges:
                                s_challenges.remove(spec_id)

                    elif challenge_response.type == JsChallengeType.N:
                        for challenge, result in challenge_response.output.results.items():
                            self._store_player_data_to_cache(result, 'n', player_url, challenge)
                            if challenge in n_challenges:
                                n_challenges.remove(challenge)

                # Raise warning if any challenge requests remain
                # Depending on type of challenge request
                help_message = (
                    'Ensure you have a supported JavaScript runtime and '
                    'challenge solver script distribution installed. '
                    'Review any warnings presented before this message. '
                    f'For more details, refer to  {_EJS_WIKI_URL}')
                if s_challenges:
                    self.report_warning(
                        f'Signature solving failed: Some formats may be missing. {help_message}',
                        video_id=video_id, only_once=True)
                if n_challenges:
                    self.report_warning(
                        f'n challenge solving failed: Some formats may be missing. {help_message}',
                        video_id=video_id, only_once=True)

                # Clear challenge sets so that any subsequent call of this function is a no-op
                s_challenges.clear()
                n_challenges.clear()