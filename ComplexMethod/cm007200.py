def built_object_repr(self):
        if self.task_id and self.is_task:
            if task := self.get_task():
                return str(task.info)
            return f"Task {self.task_id} is not running"
        if self.artifacts:
            # dump as a yaml string
            if isinstance(self.artifacts, dict):
                artifacts_ = [self.artifacts]
            elif hasattr(self.artifacts, "data"):
                artifacts_ = self.artifacts.data
            else:
                artifacts_ = self.artifacts
            artifacts = []
            for artifact in artifacts_:
                # artifacts = {k.title().replace("_", " "): v for k, v in self.artifacts.items() if v is not None}
                artifact_ = {k.title().replace("_", " "): v for k, v in artifact.items() if v is not None}
                artifacts.append(artifact_)
            return yaml.dump(artifacts, default_flow_style=False, allow_unicode=True)
        return super().built_object_repr()