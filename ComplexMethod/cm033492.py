def run(self, tmp=None, task_vars=None):
        self._supports_check_mode = True
        self._supports_async = True

        if self._play_context.check_mode:
            return {'changed': True, 'elapsed': 0, 'rebooted': True}

        if task_vars is None:
            task_vars = {}

        super(ActionModule, self).run(tmp, task_vars)

        parameters = {}
        for names, check_func in [
            (['boot_time_command'], check_type_str),
            (['connect_timeout', 'connect_timeout_sec'], _positive_float),
            (['msg'], check_type_str),
            (['post_reboot_delay', 'post_reboot_delay_sec'], _positive_float),
            (['pre_reboot_delay', 'pre_reboot_delay_sec'], _positive_float),
            (['reboot_timeout', 'reboot_timeout_sec'], _positive_float),
            (['test_command'], check_type_str),
        ]:
            for name in names:
                value = self._task.args.get(name, None)
                if value:
                    break
            else:
                value = None

            # Defaults are applied in reboot_action so skip adding to kwargs if the input wasn't set (None)
            if value is not None:
                try:
                    value = check_func(value)
                except TypeError as e:
                    raise AnsibleError("Invalid value given for '%s': %s." % (names[0], to_native(e)))

                # Setting a lower value and kill PowerShell when sending the shutdown command. Just use the defaults
                # if this is the case.
                if names[0] == 'pre_reboot_delay' and value < 2:
                    continue

                parameters[names[0]] = value

        result = reboot_host(self._task.action, self._connection, **parameters)

        # Not needed for testing and collection_name kwargs causes sanity error
        # Historical behaviour had ignore_errors=True being able to ignore unreachable hosts and not just task errors.
        # This snippet will allow that to continue but state that it will be removed in a future version and to use
        # ignore_unreachable to ignore unreachable hosts.
        # if result['unreachable'] and self._task.ignore_errors and not self._task.ignore_unreachable:
        #     dep_msg = "Host was unreachable but is being skipped because ignore_errors=True is set. In the future " \
        #               "only ignore_unreachable will be able to ignore an unreachable host for %s" % self._task.action
        #     display.deprecated(dep_msg, date="2023-05-01", collection_name="ansible.windows")
        #     result['unreachable'] = False
        #     result['failed'] = True

        return result