def validate_sig_challenge_output(challenge_output: SigChallengeOutput, challenge_input: SigChallengeInput) -> bool:
    return (
        isinstance(challenge_output, SigChallengeOutput)
        and len(challenge_output.results) == len(challenge_input.challenges)
        and all(isinstance(k, str) and isinstance(v, str) for k, v in challenge_output.results.items())
        and all(challenge in challenge_output.results for challenge in challenge_input.challenges)
    ) or 'Invalid SigChallengeOutput'