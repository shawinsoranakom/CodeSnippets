def tags_available(self, deployment_checks=False):
        return set(
            chain.from_iterable(
                check.tags for check in self.get_checks(deployment_checks)
            )
        )