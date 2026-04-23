async def connect(self) -> None:
        """Initialize E2B sandbox and start action execution server."""
        self.set_runtime_status(RuntimeStatus.STARTING_RUNTIME)

        try:
            if self.attach_to_existing and self.sandbox is None:
                try:
                    cached_sandbox_id = self.__class__._sandbox_id_cache.get(self.sid)

                    if cached_sandbox_id:
                        try:
                            self.sandbox = E2BBox(self.config.sandbox, sandbox_id=cached_sandbox_id)
                            logger.info(f"Successfully attached to existing E2B sandbox: {cached_sandbox_id}")
                        except Exception as e:
                            logger.warning(f"Failed to connect to cached sandbox {cached_sandbox_id}: {e}")
                            del self.__class__._sandbox_id_cache[self.sid]
                            self.sandbox = None

                except Exception as e:
                    logger.warning(f"Failed to attach to existing sandbox: {e}. Will create a new one.")

            # Create E2B sandbox if not provided
            if self.sandbox is None:
                try:
                    self.sandbox = E2BSandbox(self.config.sandbox)
                    sandbox_id = self.sandbox.sandbox.sandbox_id
                    logger.info(f"E2B sandbox created with ID: {sandbox_id}")

                    self.__class__._sandbox_id_cache[self.sid] = sandbox_id
                except Exception as e:
                    logger.error(f"Failed to create E2B sandbox: {e}")
                    raise

            if not isinstance(self.sandbox, (E2BSandbox, E2BBox)):
                raise ValueError("E2BRuntime requires an E2BSandbox or E2BBox")

            self.file_store = E2BFileStore(self.sandbox.filesystem)

            # E2B doesn't use action execution server - set dummy URL
            self.api_url = "direct://e2b-sandbox"

            workspace_dir = self.config.workspace_mount_path_in_sandbox
            if workspace_dir:
                try:
                    exit_code, output = self.sandbox.execute(f"sudo mkdir -p {workspace_dir}")
                    if exit_code == 0:
                        self.sandbox.execute(f"sudo chmod 777 {workspace_dir}")
                        logger.info(f"Created workspace directory: {workspace_dir}")
                    else:
                        logger.warning(f"Failed to create workspace directory: {output}")
                except Exception as e:
                    logger.warning(f"Failed to create workspace directory: {e}")

            await call_sync_from_async(self.setup_initial_env)

            self._runtime_initialized = True
            self.set_runtime_status(RuntimeStatus.READY)
            logger.info("E2B runtime connected successfully")

        except Exception as e:
            logger.error(f"Failed to connect E2B runtime: {e}")
            self.set_runtime_status(RuntimeStatus.FAILED)
            raise