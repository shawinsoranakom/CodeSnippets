def validate_nsig_challenge_output(challenge_output: NChallengeOutput, challenge_input: NChallengeInput) -> bool | str:
    if not (
        isinstance(challenge_output, NChallengeOutput)
        and len(challenge_output.results) == len(challenge_input.challenges)
        and all(isinstance(k, str) and isinstance(v, str) for k, v in challenge_output.results.items())
        and all(challenge in challenge_output.results for challenge in challenge_input.challenges)
    ):
        return 'Invalid NChallengeOutput'

    # Validate n results are valid - if they end with the input challenge then the js function returned with an exception.
    for challenge, result in challenge_output.results.items():
        if result.endswith(challenge):
            return f'n result is invalid for {challenge!r}: {result!r}'
    return True