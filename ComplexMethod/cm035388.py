async def _process_microagents_directory(
        self, repository: str, microagents_path: str
    ) -> list[MicroagentResponse]:
        """Process microagents directory and return list of microagent responses.

        Args:
            repository: Repository name in format specific to the provider
            microagents_path: Path to the microagents directory

        Returns:
            List of MicroagentResponse objects found in the directory
        """
        microagents = []

        try:
            directory_url = await self._get_microagents_directory_url(
                repository, microagents_path
            )
            directory_params = self._get_microagents_directory_params(microagents_path)
            response, _ = await self._make_request(directory_url, directory_params)

            # Handle different response structures
            items = response
            if isinstance(response, dict) and 'values' in response:
                # Bitbucket format
                items = response['values']
            elif isinstance(response, dict) and 'nodes' in response:
                # GraphQL format (if used)
                items = response['nodes']

            for item in items:
                if self._is_valid_microagent_file(item):
                    try:
                        file_name = self._get_file_name_from_item(item)
                        file_path = self._get_file_path_from_item(
                            item, microagents_path
                        )
                        microagents.append(
                            self._create_microagent_response(file_name, file_path)
                        )
                    except Exception as e:
                        logger.warning(
                            f'Error processing microagent {item.get("name", "unknown")}: {str(e)}'
                        )
        except ResourceNotFoundError:
            logger.info(
                f'No microagents directory found in {repository} at {microagents_path}'
            )
        except Exception as e:
            logger.warning(f'Error fetching microagents directory: {str(e)}')

        return microagents