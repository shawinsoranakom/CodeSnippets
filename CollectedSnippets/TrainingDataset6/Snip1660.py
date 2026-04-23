def _security_dependencies(self) -> list["Dependant"]:
        security_deps = [dep for dep in self.dependencies if dep._is_security_scheme]
        return security_deps