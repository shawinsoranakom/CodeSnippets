def _check_openhands_author(self, name, login) -> bool:
        return (
            name == 'openhands'
            or login == 'openhands'
            or login == 'openhands-agent'
            or login == 'openhands-ai'
            or login == 'openhands-staging'
            or login == 'openhands-exp'
            or (login and 'openhands' in login.lower())
        )