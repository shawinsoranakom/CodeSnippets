def _execute_webhook(self, payload):
        """ Execute the webhook for the given payload.
        The payload is a dictionnary that can be used by the `record_getter` to
        identify the record on which the automation should be run.
        """
        self.ensure_one()
        ir_logging_sudo = self.env['ir.logging'].sudo()

        # info logging is done by the ir.http logger
        msg = "Webhook #%s triggered with payload %s"
        msg_args = (self.id, payload)
        _logger.debug(msg, *msg_args)
        if self.log_webhook_calls:
            ir_logging_sudo.create(self._prepare_loggin_values(message=msg % msg_args))

        record = self.env[self.model_name]
        if self.record_getter:
            try:
                record = safe_eval.safe_eval(self.record_getter, self._get_eval_context(payload=payload))
            except Exception as e: # noqa: BLE001
                msg = "Webhook #%s could not be triggered because the record_getter failed:\n%s"
                msg_args = (self.id, traceback.format_exc())
                _logger.warning(msg, *msg_args)
                if self.log_webhook_calls:
                    ir_logging_sudo.create(self._prepare_loggin_values(message=msg % msg_args, level="ERROR"))
                raise e

        if not record.exists():
            msg = "Webhook #%s could not be triggered because no record to run it on was found."
            msg_args = (self.id,)
            _logger.warning(msg, *msg_args)
            if self.log_webhook_calls:
                ir_logging_sudo.create(self._prepare_loggin_values(message=msg % msg_args, level="ERROR"))
            raise exceptions.ValidationError(_("No record to run the automation on was found."))

        try:
            return self._process(record)
        except Exception as e: # noqa: BLE001
            msg = "Webhook #%s failed with error:\n%s"
            msg_args = (self.id, traceback.format_exc())
            _logger.warning(msg, *msg_args)
            if self.log_webhook_calls:
                ir_logging_sudo.create(self._prepare_loggin_values(message=msg % msg_args, level="ERROR"))
            raise e