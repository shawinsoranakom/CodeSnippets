def get_environment(
        self,
        version_manager_id: str,
        function_version: FunctionVersion,
        provisioning_type: InitializationType,
    ) -> Iterator[ExecutionEnvironment]:
        # Snapshot the values list before iterating to avoid skipped entries
        # that can be caused by concurrent invocations
        applicable_envs = [
            env
            for env in list(self.environments[version_manager_id].values())
            if env.initialization_type == provisioning_type
        ]
        execution_environment = None
        for environment in applicable_envs:
            try:
                environment.reserve()
                execution_environment = environment
                break
            except InvalidStatusException:
                pass

        if execution_environment is None:
            if provisioning_type == InitializationType.provisioned_concurrency:
                raise AssignmentException(
                    "No provisioned concurrency environment available despite lease."
                )
            elif provisioning_type == InitializationType.on_demand:
                with self.on_demand_start_semaphore:
                    execution_environment = self.start_environment(
                        version_manager_id, function_version
                    )
                self.environments[version_manager_id][execution_environment.id] = (
                    execution_environment
                )
                execution_environment.reserve()
            else:
                raise ValueError(f"Invalid provisioning type {provisioning_type}")

        try:
            yield execution_environment
            execution_environment.release()
        except InvalidStatusException as invalid_e:
            LOG.error("InvalidStatusException: %s", invalid_e)
        except Exception as e:
            LOG.error(
                "Failed invocation <%s>: %s", type(e), e, exc_info=LOG.isEnabledFor(logging.DEBUG)
            )
            if execution_environment.initialization_type == InitializationType.on_demand:
                self.stop_environment(execution_environment)
            else:
                # Try to restore to READY rather than stopping.
                # Transient errors (e.g., OS-level connection failures) should not
                # permanently remove healthy provisioned containers from the pool.
                try:
                    execution_environment.release()
                except InvalidStatusException:
                    self.stop_environment(execution_environment)
            raise e