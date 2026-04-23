def _validate_output(serial_str):
        try:
            minidom.parseString(serial_str)
        except Exception:
            return False
        else:
            return True