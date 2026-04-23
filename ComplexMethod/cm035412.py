def filter(self, record: logging.LogRecord) -> bool:
        # Gather sensitive values which should not ever appear in the logs.
        sensitive_values = []
        for key, value in os.environ.items():
            key_upper = key.upper()
            if (
                len(value) > 2
                and value != 'default'
                and any(s in key_upper for s in ('SECRET', '_KEY', '_CODE', '_TOKEN'))
            ):
                sensitive_values.append(value)

        # Replace sensitive values from env!
        msg = record.getMessage()
        for sensitive_value in sensitive_values:
            msg = msg.replace(sensitive_value, '******')

        # Replace obvious sensitive values from log itself...
        sensitive_patterns = [
            'api_key',
            'aws_access_key_id',
            'aws_secret_access_key',
            'e2b_api_key',
            'github_token',
            'jwt_secret',
            'modal_api_token_id',
            'modal_api_token_secret',
            'llm_api_key',
            'sandbox_env_github_token',
            'runloop_api_key',
            'daytona_api_key',
        ]

        # add env var names
        env_vars = [attr.upper() for attr in sensitive_patterns]
        sensitive_patterns.extend(env_vars)

        for attr in sensitive_patterns:
            pattern = rf"{attr}='?([\w-]+)'?"
            msg = re.sub(pattern, f"{attr}='******'", msg)

        # Update the record
        record.msg = msg
        record.args = ()

        return True