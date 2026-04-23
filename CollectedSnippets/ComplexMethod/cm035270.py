async def complete_runtime(
        self,
        runtime: Runtime,
        base_commit: str,
    ) -> dict[str, Any]:
        """Complete the runtime for the agent.

        This function is called before the runtime is used to run the agent.
        If you need to do something in the sandbox to get the correctness metric after
        the agent has run, modify this function.
        """
        logger.info('-' * 30)
        logger.info('BEGIN Runtime Completion Fn')
        logger.info('-' * 30)
        obs: Observation

        action = CmdRunAction(command='cd /workspace')
        logger.info(action, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        if not isinstance(obs, CmdOutputObservation) or obs.exit_code != 0:
            raise RuntimeError(
                f'Failed to change directory to /workspace. Observation: {obs}'
            )

        action = CmdRunAction(command='git config --global core.pager ""')
        logger.info(action, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        if not isinstance(obs, CmdOutputObservation) or obs.exit_code != 0:
            raise RuntimeError(f'Failed to set git config. Observation: {obs}')

        action = CmdRunAction(
            command='git config --global --add safe.directory /workspace'
        )
        logger.info(action, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        if not isinstance(obs, CmdOutputObservation) or obs.exit_code != 0:
            raise RuntimeError(f'Failed to set git config. Observation: {obs}')

        if self.platform == ProviderType.GITLAB and self.GITLAB_CI:
            action = CmdRunAction(command='sudo git add -A')
        else:
            action = CmdRunAction(command='git add -A')

        logger.info(action, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        if not isinstance(obs, CmdOutputObservation) or obs.exit_code != 0:
            raise RuntimeError(f'Failed to git add. Observation: {obs}')

        n_retries = 0
        git_patch = None
        while n_retries < 5:
            action = CmdRunAction(command=f'git diff --no-color --cached {base_commit}')
            action.set_hard_timeout(600 + 100 * n_retries)
            logger.info(action, extra={'msg_type': 'ACTION'})
            obs = runtime.run_action(action)
            logger.info(obs, extra={'msg_type': 'OBSERVATION'})
            n_retries += 1
            if isinstance(obs, CmdOutputObservation):
                if obs.exit_code == 0:
                    git_patch = obs.content.strip()
                    break
                else:
                    logger.info('Failed to get git diff, retrying...')
                    await asyncio.sleep(10)
            elif isinstance(obs, ErrorObservation):
                logger.error(f'Error occurred: {obs.content}. Retrying...')
                await asyncio.sleep(10)
            else:
                raise ValueError(f'Unexpected observation type: {type(obs)}')

        logger.info('-' * 30)
        logger.info('END Runtime Completion Fn')
        logger.info('-' * 30)
        return {'git_patch': git_patch}