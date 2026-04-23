def viterbi(
    observations_space: list,
    states_space: list,
    initial_probabilities: dict,
    transition_probabilities: dict,
    emission_probabilities: dict,
) -> list:
    _validation(
        observations_space,
        states_space,
        initial_probabilities,
        transition_probabilities,
        emission_probabilities,
    )
    probabilities: dict = {}
    pointers: dict = {}
    for state in states_space:
        observation = observations_space[0]
        probabilities[(state, observation)] = (
            initial_probabilities[state] * emission_probabilities[state][observation]
        )
        pointers[(state, observation)] = None

    for o in range(1, len(observations_space)):
        observation = observations_space[o]
        prior_observation = observations_space[o - 1]
        for state in states_space:
            arg_max = ""
            max_probability = -1
            for k_state in states_space:
                probability = (
                    probabilities[(k_state, prior_observation)]
                    * transition_probabilities[k_state][state]
                    * emission_probabilities[state][observation]
                )
                if probability > max_probability:
                    max_probability = probability
                    arg_max = k_state

            probabilities[(state, observation)] = (
                probabilities[(arg_max, prior_observation)]
                * transition_probabilities[arg_max][state]
                * emission_probabilities[state][observation]
            )

            pointers[(state, observation)] = arg_max

    final_observation = observations_space[len(observations_space) - 1]

    arg_max = ""
    max_probability = -1
    for k_state in states_space:
        probability = probabilities[(k_state, final_observation)]
        if probability > max_probability:
            max_probability = probability
            arg_max = k_state
    last_state = arg_max

    previous = last_state
    result = []
    for o in range(len(observations_space) - 1, -1, -1):
        result.append(previous)
        previous = pointers[previous, observations_space[o]]
    result.reverse()

    return result
