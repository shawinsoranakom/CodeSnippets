def _common_state_field_of(state_props: StateProps) -> CommonStateField:
        # TODO: use subtype loading strategy.
        match state_props.get(StateType):
            case StateType.Task:
                resource: Resource = state_props.get(Resource)
                state = state_task_for(resource)
            case StateType.Pass:
                state = StatePass()
            case StateType.Choice:
                state = StateChoice()
            case StateType.Fail:
                state = StateFail()
            case StateType.Succeed:
                state = StateSucceed()
            case StateType.Wait:
                state = StateWait()
            case StateType.Map:
                state = StateMap()
            case StateType.Parallel:
                state = StateParallel()
            case None:
                raise TypeError("No Type declaration for State in context.")
            case unknown:
                raise TypeError(
                    f"Unknown StateType value '{unknown}' in StateProps object in context."  # noqa
                )
        state.from_state_props(state_props)
        return state