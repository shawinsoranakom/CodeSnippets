def get_integration_filter(args: IntegrationConfig, targets: list[IntegrationTarget]) -> set[str]:
    """Return a list of test targets to skip based on the host(s) that will be used to run the specified test targets."""
    invalid_targets = sorted(target.name for target in targets if target.target_type not in (IntegrationTargetType.CONTROLLER, IntegrationTargetType.TARGET))

    if invalid_targets and not args.list_targets:
        message = f'''Unable to determine context for the following test targets: {", ".join(invalid_targets)}

Make sure the test targets are correctly named:

 - Modules - The target name should match the module name.
 - Plugins - The target name should be "{{plugin_type}}_{{plugin_name}}".

If necessary, context can be controlled by adding entries to the "aliases" file for a test target:

 - Add the name(s) of modules which are tested.
 - Add "context/target" for module and module_utils tests (these will run on the target host).
 - Add "context/controller" for other test types (these will run on the controller).'''

        raise ApplicationError(message)

    invalid_targets = sorted(target.name for target in targets if target.actual_type not in (IntegrationTargetType.CONTROLLER, IntegrationTargetType.TARGET))

    if invalid_targets:
        if data_context().content.is_ansible:
            display.warning(f'Unable to determine context for the following test targets: {", ".join(invalid_targets)}')
        else:
            display.warning(f'Unable to determine context for the following test targets, they will be run on the target host: {", ".join(invalid_targets)}')

    exclude: set[str] = set()

    controller_targets = [target for target in targets if target.target_type == IntegrationTargetType.CONTROLLER]
    target_targets = [target for target in targets if target.target_type == IntegrationTargetType.TARGET]

    controller_filter = get_target_filter(args, [args.controller], True)
    target_filter = get_target_filter(args, args.targets, False)

    controller_filter.filter_targets(controller_targets, exclude)
    target_filter.filter_targets(target_targets, exclude)

    return exclude