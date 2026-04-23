def _update_logger_level(self, logger_name, new_level, available_log_levels, handler_folder=False):
        """Update (if necessary) Odoo's configuration and logger to the given logger_name to the given level.
        The responsibility of saving the config file is not managed here.

        :param logger_name: name of the logging logger to change level
        :param new_level: new log level to set for this logger
        :param available_log_levels: iterable of logs levels allowed (for initial check)
        :param str handler_folder: optional string of the IoT handler folder name ('interfaces' or 'drivers')
        """
        # We store the timestamp to reset the log level to warning after a week (7 days * 24 hours * 3600 seconds)
        # This is to avoid sending polluted logs with debug messages to the db
        conf = {'log_level_reset_timestamp': str(time.time() + 7 * 24 * 3600)}

        if new_level not in available_log_levels:
            _logger.warning('Unknown level to set on logger %s: %s', logger_name, new_level)
            return

        if handler_folder:
            logger = self._get_iot_handler_logger(logger_name, handler_folder)
            if not logger:
                _logger.warning('Unable to change log level for logger %s as logger missing', logger_name)
                return
            logger_name = logger.name

        ODOO_TOOL_CONFIG_HANDLER_NAME = 'log_handler'
        LOG_HANDLERS = (helpers.get_conf(ODOO_TOOL_CONFIG_HANDLER_NAME, section='options') or []).split(',')
        LOGGER_PREFIX = logger_name + ':'
        IS_NEW_LEVEL_PARENT = new_level == 'parent'

        if not IS_NEW_LEVEL_PARENT:
            intended_to_find = LOGGER_PREFIX + new_level.upper()
            if intended_to_find in LOG_HANDLERS:
                # There is nothing to do, the entry is already inside
                return

        # We remove every occurrence for the given logger
        log_handlers_without_logger = [
            log_handler for log_handler in LOG_HANDLERS if not log_handler.startswith(LOGGER_PREFIX)
        ]

        if IS_NEW_LEVEL_PARENT:
            # We must check that there is no existing entries using this logger (whatever the level)
            if len(log_handlers_without_logger) == len(LOG_HANDLERS):
                return

        # We add if necessary new logger entry
        # If it is "parent" it means we want it to inherit from the parent logger.
        # In order to do this we have to make sure that no entries for the logger exists in the
        # `log_handler` (which is the case at this point as long as we don't re-add an entry)
        new_level_upper_case = new_level.upper()
        if not IS_NEW_LEVEL_PARENT:
            new_entry = LOGGER_PREFIX + new_level_upper_case
            log_handlers_without_logger.append(new_entry)
            _logger.debug('Adding to odoo config log_handler: %s', new_entry)
        conf[ODOO_TOOL_CONFIG_HANDLER_NAME] = ','.join(log_handlers_without_logger)

        # Update the logger dynamically
        real_new_level = logging.NOTSET if IS_NEW_LEVEL_PARENT else new_level_upper_case
        _logger.debug('Change logger %s level to %s', logger_name, real_new_level)
        logging.getLogger(logger_name).setLevel(real_new_level)

        helpers.update_conf(conf, section='options')