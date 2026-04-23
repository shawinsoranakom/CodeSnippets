async def _ensure_sandbox(self) -> Sandbox:
        """Ensure we have a valid sandbox instance, retrieving it from the project if needed."""
        if self._sandbox is None:
            # Get or start the sandbox
            try:
                self._sandbox = create_sandbox(password=config.daytona.VNC_password)
                # Log URLs if not already printed
                if not SandboxToolsBase._urls_printed:
                    vnc_link = self._sandbox.get_preview_link(6080)
                    website_link = self._sandbox.get_preview_link(8080)

                    vnc_url = (
                        vnc_link.url if hasattr(vnc_link, "url") else str(vnc_link)
                    )
                    website_url = (
                        website_link.url
                        if hasattr(website_link, "url")
                        else str(website_link)
                    )

                    print("\033[95m***")
                    print(f"VNC URL: {vnc_url}")
                    print(f"Website URL: {website_url}")
                    print("***\033[0m")
                    SandboxToolsBase._urls_printed = True
            except Exception as e:
                logger.error(f"Error retrieving or starting sandbox: {str(e)}")
                raise e
        else:
            if (
                self._sandbox.state == SandboxState.ARCHIVED
                or self._sandbox.state == SandboxState.STOPPED
            ):
                logger.info(f"Sandbox is in {self._sandbox.state} state. Starting...")
                try:
                    daytona.start(self._sandbox)
                    # Wait a moment for the sandbox to initialize
                    # sleep(5)
                    # Refresh sandbox state after starting

                    # Start supervisord in a session when restarting
                    start_supervisord_session(self._sandbox)
                except Exception as e:
                    logger.error(f"Error starting sandbox: {e}")
                    raise e
        return self._sandbox