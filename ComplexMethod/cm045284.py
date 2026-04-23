async def stop(self) -> None:
        """(Experimental) Stop the code executor.

        Stops the Docker container and cleans up any temporary files (if they were created), along with the temporary directory.
        The method first waits for all cancellation tasks to finish before stopping the container. Finally it marks the executor as not running.
        If the container is not running, the method does nothing.
        """
        if not self._running:
            return

        if self._temp_dir is not None:
            self._temp_dir.cleanup()
            self._temp_dir = None

        client = docker.from_env()
        try:
            try:
                container = await asyncio.to_thread(client.containers.get, self.container_name)
            except NotFound:
                logging.debug(f"Container {self.container_name} not found during stop...")
                self._running = False
                self._cancellation_futures.clear()
                return

            if self._cancellation_futures:
                if not self._loop or self._loop.is_closed():
                    logging.warning(
                        f"Executor loop ({self._loop!r}) is closed or unavailable. Cannot reliably wait for "
                        f"{len(self._cancellation_futures)} cancellation futures."
                    )
                    self._cancellation_futures.clear()
                else:
                    # concurrent.futures.Future -> asyncio.Future
                    asyncio_futures = [asyncio.wrap_future(f, loop=self._loop) for f in self._cancellation_futures]

                    if asyncio_futures:
                        logging.debug(
                            f"Waiting for {len(asyncio_futures)} cancellation futures to complete on loop {self._loop!r}..."
                        )
                        results = await asyncio.gather(*asyncio_futures, return_exceptions=True)
                        for i, result in enumerate(results):
                            original_future = self._cancellation_futures[i]
                            if isinstance(result, Exception):
                                logging.warning(f"Cancellation future {original_future!r} failed: {result}")
                            else:
                                logging.debug(f"Cancellation future {original_future!r} completed successfully.")
                    else:
                        logging.debug("No valid cancellation futures to await.")

                    self._cancellation_futures.clear()

            logging.debug(f"Stopping container {self.container_name}...")
            await asyncio.to_thread(container.stop)
            logging.debug(f"Container {self.container_name} stopped.")

        except DockerException as e:
            logging.error(f"Docker error while stopping container {self.container_name}: {e}")
        except Exception as e:
            logging.exception(f"Unexpected error during stop operation for container {self.container_name}: {e}")
        finally:
            self._running = False
            self._cancellation_futures.clear()