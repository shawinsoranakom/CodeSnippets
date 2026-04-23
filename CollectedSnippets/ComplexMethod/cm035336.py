def observation_from_dict(observation: dict) -> Observation:
    observation = observation.copy()
    if 'observation' not in observation:
        raise KeyError(f"'observation' key is not found in {observation=}")
    observation_class = OBSERVATION_TYPE_TO_CLASS.get(observation['observation'])
    if observation_class is None:
        raise KeyError(
            f"'{observation['observation']=}' is not defined. Available observations: {OBSERVATION_TYPE_TO_CLASS.keys()}"
        )
    observation.pop('observation')
    observation.pop('message', None)
    content = observation.pop('content', '')
    extras = copy.deepcopy(observation.pop('extras', {}))

    extras = handle_observation_deprecated_extras(extras)

    # convert metadata to CmdOutputMetadata if it is a dict
    if observation_class is CmdOutputObservation:
        if 'metadata' in extras and isinstance(extras['metadata'], dict):
            extras['metadata'] = CmdOutputMetadata(**extras['metadata'])
        elif 'metadata' in extras and isinstance(extras['metadata'], CmdOutputMetadata):
            pass
        else:
            extras['metadata'] = CmdOutputMetadata()

    if observation_class is RecallObservation:
        # handle the Enum conversion
        if 'recall_type' in extras:
            extras['recall_type'] = RecallType(extras['recall_type'])

        # convert dicts in microagent_knowledge to MicroagentKnowledge objects
        if 'microagent_knowledge' in extras and isinstance(
            extras['microagent_knowledge'], list
        ):
            extras['microagent_knowledge'] = [
                MicroagentKnowledge(**item) if isinstance(item, dict) else item
                for item in extras['microagent_knowledge']
            ]

    obs = observation_class(content=content, **extras)
    assert isinstance(obs, Observation)
    return obs