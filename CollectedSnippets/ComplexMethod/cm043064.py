async def process_user_hooks_with_manager(
    hooks_input: Dict[str, str],
    hook_manager: UserHookManager
) -> Tuple[Dict[str, Callable], List[Dict]]:
    """
    Process and compile user-provided hook functions with existing manager

    Args:
        hooks_input: Dictionary mapping hook points to code strings
        hook_manager: Existing UserHookManager instance

    Returns:
        Tuple of (compiled_hooks, validation_errors)
    """

    wrapper = IsolatedHookWrapper(hook_manager)
    compiled_hooks = {}
    validation_errors = []

    for hook_point, hook_code in hooks_input.items():
        # Skip empty hooks
        if not hook_code or not hook_code.strip():
            continue

        # Validate hook point
        if hook_point not in UserHookManager.HOOK_SIGNATURES:
            validation_errors.append({
                'hook_point': hook_point,
                'error': f'Unknown hook point. Valid points: {", ".join(UserHookManager.HOOK_SIGNATURES.keys())}',
                'code_preview': hook_code[:100] + '...' if len(hook_code) > 100 else hook_code
            })
            continue

        # Validate structure
        is_valid, message = hook_manager.validate_hook_structure(hook_code, hook_point)
        if not is_valid:
            validation_errors.append({
                'hook_point': hook_point,
                'error': message,
                'code_preview': hook_code[:100] + '...' if len(hook_code) > 100 else hook_code
            })
            continue

        # Compile the hook
        hook_func = hook_manager.compile_hook(hook_code, hook_point)
        if hook_func:
            # Wrap with error isolation
            wrapped_hook = wrapper.create_hook_wrapper(hook_func, hook_point)
            compiled_hooks[hook_point] = wrapped_hook
            logger.info(f"Successfully compiled hook for {hook_point}")
        else:
            validation_errors.append({
                'hook_point': hook_point,
                'error': 'Failed to compile hook function - check syntax and structure',
                'code_preview': hook_code[:100] + '...' if len(hook_code) > 100 else hook_code
            })

    return compiled_hooks, validation_errors