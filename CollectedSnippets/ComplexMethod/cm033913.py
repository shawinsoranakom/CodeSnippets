def validate_reboot(self, distribution, original_connection_timeout=None, action_kwargs=None):
        display.vvv('{action}: validating reboot'.format(action=self._task.action))
        result = {}

        try:
            # keep on checking system boot_time with short connection responses
            reboot_timeout = int(self._task.args.get('reboot_timeout', self._task.args.get('reboot_timeout_sec', self.DEFAULT_REBOOT_TIMEOUT)))

            self.do_until_success_or_timeout(
                action=self.check_boot_time,
                action_desc="last boot time check",
                reboot_timeout=reboot_timeout,
                distribution=distribution,
                action_kwargs=action_kwargs)

            # Get the connect_timeout set on the connection to compare to the original
            try:
                connect_timeout = self._connection.get_option('connection_timeout')
            except KeyError:
                try:
                    connect_timeout = self._connection.get_option('timeout')
                except KeyError:
                    pass
            else:
                if original_connection_timeout != connect_timeout:
                    try:
                        display.debug("{action}: setting connect_timeout/timeout back to original value of {value}".format(action=self._task.action,
                                                                                                                           value=original_connection_timeout))
                        try:
                            self._connection.set_option("connection_timeout", original_connection_timeout)
                        except AnsibleError:
                            try:
                                self._connection.set_option("timeout", original_connection_timeout)
                            except AnsibleError:
                                raise
                        # reset the connection to clear the custom connection timeout
                        self._connection.reset()
                    except (AnsibleError, AttributeError) as e:
                        display.debug("{action}: failed to reset connection_timeout back to default: {error}".format(action=self._task.action,
                                                                                                                     error=to_text(e)))

            # finally run test command to ensure everything is working
            # FUTURE: add a stability check (system must remain up for N seconds) to deal with self-multi-reboot updates
            self.do_until_success_or_timeout(
                action=self.run_test_command,
                action_desc="post-reboot test command",
                reboot_timeout=reboot_timeout,
                distribution=distribution,
                action_kwargs=action_kwargs)

            result['rebooted'] = True
            result['changed'] = True

        except TimedOutException as toex:
            result['failed'] = True
            result['rebooted'] = True
            result['msg'] = to_text(toex)
            return result

        return result