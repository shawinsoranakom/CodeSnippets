def _validate_output(serial_str):
        try:
            json.loads(serial_str)
        except Exception:
            return False
        else:
            return True