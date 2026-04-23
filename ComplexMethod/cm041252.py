def run_stage(self, stage: Stage) -> list[Script]:
        """
        Runs all scripts in the given stage.

        :param stage: the stage to run
        :return: the scripts that were in the stage
        """
        scripts = self.scripts.get(stage, [])

        if self.stage_completed[stage]:
            LOG.debug("Stage %s already completed, skipping", stage)
            return scripts

        try:
            for script in scripts:
                LOG.debug("Running %s script %s", script.stage, script.path)

                env_original = os.environ.copy()

                try:
                    script.state = State.RUNNING
                    runner = self.get_script_runner(script.path)
                    runner.run(script.path)
                except Exception as e:
                    script.state = State.ERROR
                    if LOG.isEnabledFor(logging.DEBUG):
                        LOG.exception("Error while running script %s", script)
                    else:
                        LOG.error("Error while running script %s: %s", script, e)
                else:
                    script.state = State.SUCCESSFUL
                finally:
                    # Discard env variables overridden in startup script that may cause side-effects
                    for env_var in (
                        "AWS_ACCESS_KEY_ID",
                        "AWS_SECRET_ACCESS_KEY",
                        "AWS_SESSION_TOKEN",
                        "AWS_DEFAULT_REGION",
                        "AWS_PROFILE",
                        "AWS_REGION",
                    ):
                        if env_var in env_original:
                            os.environ[env_var] = env_original[env_var]
                        else:
                            os.environ.pop(env_var, None)
        finally:
            self.stage_completed[stage] = True

        return scripts