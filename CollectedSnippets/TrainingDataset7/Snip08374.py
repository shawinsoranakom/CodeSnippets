def tag_exists(self, tag, include_deployment_checks=False):
        return tag in self.tags_available(include_deployment_checks)