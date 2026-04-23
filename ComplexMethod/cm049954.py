def _is_valid_adyen_request_data(self, provided_data, expected_data):
        if not isinstance(provided_data, dict) or set(provided_data.keys()) != set(expected_data.keys()):
            return False

        for provided_key, provided_value in provided_data.items():
            expected_value = expected_data[provided_key]
            if expected_value == UNPREDICTABLE_ADYEN_DATA:
                continue
            if isinstance(expected_value, dict):
                if not self._is_valid_adyen_request_data(provided_value, expected_value):
                    return False
            else:
                if provided_value != expected_value:
                    return False
        return True