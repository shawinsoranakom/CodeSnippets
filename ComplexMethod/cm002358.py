def retrieve_available_artifacts():
    class Artifact:
        def __init__(self, name: str, single_gpu: bool = False, multi_gpu: bool = False):
            self.name = name
            self.single_gpu = single_gpu
            self.multi_gpu = multi_gpu
            self.paths = []

        def __str__(self):
            return self.name

        def add_path(self, path: str, gpu: str | None = None):
            self.paths.append({"name": self.name, "path": path, "gpu": gpu})

    _available_artifacts: dict[str, Artifact] = {}

    directories = filter(os.path.isdir, os.listdir())
    for directory in directories:
        artifact_name = directory

        name_parts = artifact_name.split("_postfix_")
        if len(name_parts) > 1:
            artifact_name = name_parts[0]

        if artifact_name.startswith("single-gpu"):
            artifact_name = artifact_name[len("single-gpu") + 1 :]

            if artifact_name in _available_artifacts:
                _available_artifacts[artifact_name].single_gpu = True
            else:
                _available_artifacts[artifact_name] = Artifact(artifact_name, single_gpu=True)

            _available_artifacts[artifact_name].add_path(directory, gpu="single")

        elif artifact_name.startswith("multi-gpu"):
            artifact_name = artifact_name[len("multi-gpu") + 1 :]

            if artifact_name in _available_artifacts:
                _available_artifacts[artifact_name].multi_gpu = True
            else:
                _available_artifacts[artifact_name] = Artifact(artifact_name, multi_gpu=True)

            _available_artifacts[artifact_name].add_path(directory, gpu="multi")
        else:
            if artifact_name not in _available_artifacts:
                _available_artifacts[artifact_name] = Artifact(artifact_name)

            _available_artifacts[artifact_name].add_path(directory)

    return _available_artifacts