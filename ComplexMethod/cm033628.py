def wait(self) -> None:
        """Wait for the instance to be ready. Executed before delegation for the controller and after delegation for targets."""
        if not self.controller:
            con = self.get_controller_target_connections()[0]
            last_error = ''

            for dummy in range(1, 10):
                try:
                    con.run(['id'], capture=True)
                except SubprocessError as ex:
                    if 'Permission denied' in ex.message:
                        raise

                    last_error = str(ex)
                    time.sleep(1)
                else:
                    return

            display.info('Checking SSH debug output...')
            display.info(last_error)

            if not self.args.delegate and not self.args.host_path:

                def callback() -> None:
                    """Callback to run during error display."""
                    self.on_target_failure()  # when the controller is not delegated, report failures immediately

            else:
                callback = None

            raise HostConnectionError(f'Timeout waiting for {self.config.name} container {self.container_name}.', callback)