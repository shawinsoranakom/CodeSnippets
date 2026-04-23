def _validate_output(serial_str):
        try:
            for line in serial_str.split("\n"):
                if line:
                    json.loads(line)
        except Exception:
            return False
        else:
            return True