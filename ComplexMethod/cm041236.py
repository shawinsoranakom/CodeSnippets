def _check_logs(func_name: str, expected_lines: list[str] = None) -> list[str]:
        if not expected_lines:
            expected_lines = []
        log_events = get_lambda_logs(func_name, logs_client=aws_client.logs)
        log_messages = [e["message"] for e in log_events]
        for line in expected_lines:
            if ".*" in line:
                found = [re.match(line, m, flags=re.DOTALL) for m in log_messages]
                if any(found):
                    continue
            assert line in log_messages
        return log_messages