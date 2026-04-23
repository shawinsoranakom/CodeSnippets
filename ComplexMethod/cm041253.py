def _find_scripts(self) -> dict[Stage, list[Script]]:
        scripts = {}

        if self.script_root is None:
            LOG.debug("Unable to discover init scripts as script_root is None")
            return {}

        for stage in Stage:
            scripts[stage] = []

            stage_dir = self._stage_directories[stage]
            if not stage_dir:
                continue

            stage_path = os.path.join(self.script_root, stage_dir)
            if not os.path.isdir(stage_path):
                continue

            for root, dirs, files in os.walk(stage_path, topdown=True):
                # from the docs: "When topdown is true, the caller can modify the dirnames list in-place"
                dirs.sort()
                files.sort()
                for file in files:
                    script_path = os.path.abspath(os.path.join(root, file))
                    if not os.path.isfile(script_path):
                        continue

                    # only add the script if there's a runner for it
                    if not self.has_script_runner(script_path):
                        LOG.debug("No runner available for script %s", script_path)
                        continue

                    scripts[stage].append(Script(path=script_path, stage=stage))
        LOG.debug("Init scripts discovered: %s", scripts)

        return scripts