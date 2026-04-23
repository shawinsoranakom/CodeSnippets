def viterbi(
    observations_space: list,
    states_space: list,
    initial_probabilities: dict,
    transition_probabilities: dict,
    emission_probabilities: dict,
) -> list:
    """
    Viterbi Algorithm, to find the most likely path of
    states from the start and the expected output.

    https://en.wikipedia.org/wiki/Viterbi_algorithm

    Wikipedia example

    >>> observations = ["normal", "cold", "dizzy"]
    >>> states = ["Healthy", "Fever"]
    >>> start_p = {"Healthy": 0.6, "Fever": 0.4}
    >>> trans_p = {
    ...     "Healthy": {"Healthy": 0.7, "Fever": 0.3},
    ...     "Fever": {"Healthy": 0.4, "Fever": 0.6},
    ... }
    >>> emit_p = {
    ...     "Healthy": {"normal": 0.5, "cold": 0.4, "dizzy": 0.1},
    ...     "Fever": {"normal": 0.1, "cold": 0.3, "dizzy": 0.6},
    ... }
    >>> viterbi(observations, states, start_p, trans_p, emit_p)
    ['Healthy', 'Healthy', 'Fever']
    >>> viterbi((), states, start_p, trans_p, emit_p)
    Traceback (most recent call last):
        ...
    ValueError: There's an empty parameter
    >>> viterbi(observations, (), start_p, trans_p, emit_p)
    Traceback (most recent call last):
        ...
    ValueError: There's an empty parameter
    >>> viterbi(observations, states, {}, trans_p, emit_p)
    Traceback (most recent call last):
        ...
    ValueError: There's an empty parameter
    >>> viterbi(observations, states, start_p, {}, emit_p)
    Traceback (most recent call last):
        ...
    ValueError: There's an empty parameter
    >>> viterbi(observations, states, start_p, trans_p, {})
    Traceback (most recent call last):
        ...
    ValueError: There's an empty parameter
    >>> viterbi("invalid", states, start_p, trans_p, emit_p)
    Traceback (most recent call last):
        ...
    ValueError: observations_space must be a list
    >>> viterbi(["valid", 123], states, start_p, trans_p, emit_p)
    Traceback (most recent call last):
        ...
    ValueError: observations_space must be a list of strings
    >>> viterbi(observations, "invalid", start_p, trans_p, emit_p)
    Traceback (most recent call last):
        ...
    ValueError: states_space must be a list
    >>> viterbi(observations, ["valid", 123], start_p, trans_p, emit_p)
    Traceback (most recent call last):
        ...
    ValueError: states_space must be a list of strings
    >>> viterbi(observations, states, "invalid", trans_p, emit_p)
    Traceback (most recent call last):
        ...
    ValueError: initial_probabilities must be a dict
    >>> viterbi(observations, states, {2:2}, trans_p, emit_p)
    Traceback (most recent call last):
        ...
    ValueError: initial_probabilities all keys must be strings
    >>> viterbi(observations, states, {"a":2}, trans_p, emit_p)
    Traceback (most recent call last):
        ...
    ValueError: initial_probabilities all values must be float
    >>> viterbi(observations, states, start_p, "invalid", emit_p)
    Traceback (most recent call last):
        ...
    ValueError: transition_probabilities must be a dict
    >>> viterbi(observations, states, start_p, {"a":2}, emit_p)
    Traceback (most recent call last):
        ...
    ValueError: transition_probabilities all values must be dict
    >>> viterbi(observations, states, start_p, {2:{2:2}}, emit_p)
    Traceback (most recent call last):
        ...
    ValueError: transition_probabilities all keys must be strings
    >>> viterbi(observations, states, start_p, {"a":{2:2}}, emit_p)
    Traceback (most recent call last):
        ...
    ValueError: transition_probabilities all keys must be strings
    >>> viterbi(observations, states, start_p, {"a":{"b":2}}, emit_p)
    Traceback (most recent call last):
        ...
    ValueError: transition_probabilities nested dictionary all values must be float
    >>> viterbi(observations, states, start_p, trans_p, "invalid")
    Traceback (most recent call last):
        ...
    ValueError: emission_probabilities must be a dict
    >>> viterbi(observations, states, start_p, trans_p, None)
    Traceback (most recent call last):
        ...
    ValueError: There's an empty parameter

    """
    _validation(
        observations_space,
        states_space,
        initial_probabilities,
        transition_probabilities,
        emission_probabilities,
    )
    # Creates data structures and fill initial step
    probabilities: dict = {}
    pointers: dict = {}
    for state in states_space:
        observation = observations_space[0]
        probabilities[(state, observation)] = (
            initial_probabilities[state] * emission_probabilities[state][observation]
        )
        pointers[(state, observation)] = None

    # Fills the data structure with the probabilities of
    # different transitions and pointers to previous states
    for o in range(1, len(observations_space)):
        observation = observations_space[o]
        prior_observation = observations_space[o - 1]
        for state in states_space:
            # Calculates the argmax for probability function
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

            # Update probabilities and pointers dicts
            probabilities[(state, observation)] = (
                probabilities[(arg_max, prior_observation)]
                * transition_probabilities[arg_max][state]
                * emission_probabilities[state][observation]
            )

            pointers[(state, observation)] = arg_max

    # The final observation
    final_observation = observations_space[len(observations_space) - 1]

    # argmax for given final observation
    arg_max = ""
    max_probability = -1
    for k_state in states_space:
        probability = probabilities[(k_state, final_observation)]
        if probability > max_probability:
            max_probability = probability
            arg_max = k_state
    last_state = arg_max

    # Process pointers backwards
    previous = last_state
    result = []
    for o in range(len(observations_space) - 1, -1, -1):
        result.append(previous)
        previous = pointers[previous, observations_space[o]]
    result.reverse()

    return result