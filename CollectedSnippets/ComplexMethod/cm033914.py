def run(self, tmp=None, task_vars=None):
        self._supports_check_mode = True

        # If running with local connection, fail so we don't reboot ourselves
        if self._connection.transport == 'local':
            msg = 'Running {0} with local connection would reboot the control node.'.format(self._task.action)
            return {'changed': False, 'elapsed': 0, 'rebooted': False, 'failed': True, 'msg': msg}

        if self._task.check_mode:
            return {'changed': True, 'elapsed': 0, 'rebooted': True}

        if task_vars is None:
            task_vars = {}

        self.deprecated_args()

        result = super(ActionModule, self).run(tmp, task_vars)

        if result.get('skipped', False) or result.get('failed', False):
            return result

        distribution = self.get_distribution(task_vars)

        # Get current boot time
        try:
            previous_boot_time = self.get_system_boot_time(distribution)
        except Exception as e:
            result['failed'] = True
            result['reboot'] = False
            result['msg'] = to_text(e)
            return result

        # Get the original connection_timeout option var so it can be reset after
        original_connection_timeout = None

        display.debug("{action}: saving original connect_timeout of {timeout}".format(action=self._task.action, timeout=original_connection_timeout))
        try:
            original_connection_timeout = self._connection.get_option('connection_timeout')
        except KeyError:
            try:
                original_connection_timeout = self._connection.get_option('timeout')
            except KeyError:
                display.debug("{action}: connect_timeout connection option has not been set".format(action=self._task.action))

        # Initiate reboot
        reboot_result = self.perform_reboot(task_vars, distribution)

        if reboot_result['failed']:
            result = reboot_result
            elapsed = datetime.now(timezone.utc) - reboot_result['start']
            result['elapsed'] = elapsed.seconds
            return result

        if self.post_reboot_delay != 0:
            display.debug("{action}: waiting an additional {delay} seconds".format(action=self._task.action, delay=self.post_reboot_delay))
            display.vvv("{action}: waiting an additional {delay} seconds".format(action=self._task.action, delay=self.post_reboot_delay))
            time.sleep(self.post_reboot_delay)

        # Make sure reboot was successful
        result = self.validate_reboot(distribution, original_connection_timeout, action_kwargs={'previous_boot_time': previous_boot_time})

        elapsed = datetime.now(timezone.utc) - reboot_result['start']
        result['elapsed'] = elapsed.seconds

        return result