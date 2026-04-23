def _validate_output(serial_str):
        try:
            yaml.safe_load(StringIO(serial_str))
        except Exception:
            return False
        else:
            return True