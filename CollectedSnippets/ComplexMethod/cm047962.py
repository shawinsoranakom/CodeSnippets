def _twilio_error_code_to_odoo_state(self, response_json):
        error_code = response_json.get('code') or response_json.get('error_code')
        # number issues
        if error_code in (21211, 21614, 21265):  # See https://www.twilio.com/docs/errors/xxxxx
            return "wrong_number_format"
        elif error_code == 21604:
            # A "To" phone number is required
            return "sms_number_missing"
        elif error_code == 21266:
            return "twilio_from_to"
        elif error_code == 21603:
            return "twilio_from_missing"
        # configuration
        elif error_code == 21608:
            return "twilio_acc_unverified"
        elif error_code == 21609:
            # Twilio StatusCallback URL is incorrect
            return "twilio_callback"
        _logger.warning('Twilio SMS: Unknown error "%s" (code: %s)', response_json.get('message'), error_code)
        return "unknown"