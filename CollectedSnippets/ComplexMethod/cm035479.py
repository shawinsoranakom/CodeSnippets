async def delete(cls, conversation_id: str) -> None:
        """Delete the runtime for a conversation."""
        if conversation_id in _RUNNING_SERVERS:
            logger.info(f'Deleting LocalRuntime for conversation {conversation_id}')
            server_info = _RUNNING_SERVERS[conversation_id]

            # Signal the log thread to exit
            server_info.log_thread_exit_event.set()

            # Terminate the server process
            if server_info.process:
                server_info.process.terminate()
                try:
                    server_info.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    server_info.process.kill()

            # Wait for the log thread to finish
            server_info.log_thread.join(timeout=5)

            # Remove from global dictionary
            del _RUNNING_SERVERS[conversation_id]
            logger.info(f'LocalRuntime for conversation {conversation_id} deleted')

        # Also clean up any warm servers if this is the last conversation being deleted
        if not _RUNNING_SERVERS:
            logger.info('No active conversations, cleaning up warm servers')
            for server_info in _WARM_SERVERS[:]:
                # Signal the log thread to exit
                server_info.log_thread_exit_event.set()

                # Terminate the server process
                if server_info.process:
                    server_info.process.terminate()
                    try:
                        server_info.process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        server_info.process.kill()

                # Wait for the log thread to finish
                server_info.log_thread.join(timeout=5)

                # Clean up temp workspace
                if server_info.temp_workspace:
                    shutil.rmtree(server_info.temp_workspace)

                # Remove from warm servers list
                _WARM_SERVERS.remove(server_info)

            logger.info('All warm servers cleaned up')