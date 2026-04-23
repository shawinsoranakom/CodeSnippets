def disable(self):
        self.registry.registered_checks = self.old_checks
        self.registry.deployment_checks = self.old_deployment_checks