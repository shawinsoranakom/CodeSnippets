def update_log_level(self, name, value):
        if not name.startswith(IOT_LOGGING_PREFIX) and name != 'log-to-server':
            return {
                'status': 'error',
                'message': 'Invalid logger name',
            }

        if name == 'log-to-server':
            check_and_update_odoo_config_log_to_server_option(value)

        name = name[len(IOT_LOGGING_PREFIX):]
        if name == 'root':
            self._update_logger_level('', value, AVAILABLE_LOG_LEVELS)
        elif name == 'odoo':
            self._update_logger_level('odoo', value, AVAILABLE_LOG_LEVELS)
            self._update_logger_level('werkzeug', value if value != 'debug' else 'info', AVAILABLE_LOG_LEVELS)
        elif name.startswith(INTERFACE_PREFIX):
            logger_name = name[len(INTERFACE_PREFIX):]
            self._update_logger_level(logger_name, value, AVAILABLE_LOG_LEVELS_WITH_PARENT, 'interfaces')
        elif name.startswith(DRIVER_PREFIX):
            logger_name = name[len(DRIVER_PREFIX):]
            self._update_logger_level(logger_name, value, AVAILABLE_LOG_LEVELS_WITH_PARENT, 'drivers')
        else:
            _logger.warning('Unhandled iot logger: %s', name)

        return {
            'status': 'success',
            'message': 'Logger level updated',
        }