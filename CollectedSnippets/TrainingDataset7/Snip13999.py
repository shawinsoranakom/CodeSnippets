def __init__(self, new_checks, deployment_checks=None):
        from django.core.checks.registry import registry

        self.registry = registry
        self.new_checks = new_checks
        self.deployment_checks = deployment_checks
        super().__init__()