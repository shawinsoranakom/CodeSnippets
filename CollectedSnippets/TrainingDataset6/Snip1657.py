def _uses_scopes(self) -> bool:
        if self.own_oauth_scopes:
            return True
        if self.security_scopes_param_name is not None:
            return True
        if self._is_security_scheme:
            return True
        for sub_dep in self.dependencies:
            if sub_dep._uses_scopes:
                return True
        return False