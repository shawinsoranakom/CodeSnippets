def action_from_dict(action: dict) -> Action:
    if not isinstance(action, dict):
        raise LLMMalformedActionError('action must be a dictionary')
    action = action.copy()
    if 'action' not in action:
        raise LLMMalformedActionError(f"'action' key is not found in {action=}")
    if not isinstance(action['action'], str):
        raise LLMMalformedActionError(
            f"'{action['action']=}' is not defined. Available actions: {ACTION_TYPE_TO_CLASS.keys()}"
        )
    action_class = ACTION_TYPE_TO_CLASS.get(action['action'])
    if action_class is None:
        raise LLMMalformedActionError(
            f"'{action['action']=}' is not defined. Available actions: {ACTION_TYPE_TO_CLASS.keys()}"
        )
    args = action.get('args', {})
    # Remove timestamp from args if present
    timestamp = args.pop('timestamp', None)

    # compatibility for older event streams
    # is_confirmed has been renamed to confirmation_state
    is_confirmed = args.pop('is_confirmed', None)
    if is_confirmed is not None:
        args['confirmation_state'] = is_confirmed

    # images_urls has been renamed to image_urls
    if 'images_urls' in args:
        args['image_urls'] = args.pop('images_urls')

    # Handle security_risk deserialization
    if 'security_risk' in args and args['security_risk'] is not None:
        try:
            # Convert numeric value (int) back to enum
            args['security_risk'] = ActionSecurityRisk(args['security_risk'])
        except (ValueError, TypeError):
            # If conversion fails, remove the invalid value
            args.pop('security_risk')

    # handle deprecated args
    args = handle_action_deprecated_args(args)

    try:
        decoded_action = action_class(**args)
        if 'timeout' in action:
            blocking = args.get('blocking', False)
            decoded_action.set_hard_timeout(action['timeout'], blocking=blocking)

        # Set timestamp if it was provided
        if timestamp:
            decoded_action._timestamp = timestamp

    except TypeError as e:
        raise LLMMalformedActionError(
            f'action={action} has the wrong arguments: {str(e)}'
        )
    assert isinstance(decoded_action, Action)
    return decoded_action