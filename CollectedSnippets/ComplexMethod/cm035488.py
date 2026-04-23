def execute(self, action: CmdRunAction) -> CmdOutputObservation | ErrorObservation:
        """Execute a command in the bash session."""
        if not self._initialized:
            raise RuntimeError('Bash session is not initialized')

        # Strip the command of any leading/trailing whitespace
        logger.debug(f'RECEIVED ACTION: {action}')
        command = action.command.strip()
        is_input: bool = action.is_input

        # If the previous command is not completed, we need to check if the command is empty
        if self.prev_status not in {
            BashCommandStatus.CONTINUE,
            BashCommandStatus.NO_CHANGE_TIMEOUT,
            BashCommandStatus.HARD_TIMEOUT,
        }:
            if command == '':
                return CmdOutputObservation(
                    content='ERROR: No previous running command to retrieve logs from.',
                    command='',
                    metadata=CmdOutputMetadata(),
                )
            if is_input:
                return CmdOutputObservation(
                    content='ERROR: No previous running command to interact with.',
                    command='',
                    metadata=CmdOutputMetadata(),
                )

        # Check if the command is a single command or multiple commands
        splited_commands = split_bash_commands(command)
        if len(splited_commands) > 1:
            return ErrorObservation(
                content=(
                    f'ERROR: Cannot execute multiple commands at once.\n'
                    f'Please run each command separately OR chain them into a single command via && or ;\n'
                    f'Provided commands:\n{"\n".join(f"({i + 1}) {cmd}" for i, cmd in enumerate(splited_commands))}'
                )
            )

        # Get initial state before sending command
        initial_pane_output = self._get_pane_content()
        initial_ps1_matches = CmdOutputMetadata.matches_ps1_metadata(
            initial_pane_output
        )
        initial_ps1_count = len(initial_ps1_matches)
        logger.debug(f'Initial PS1 count: {initial_ps1_count}')

        start_time = time.time()
        last_change_time = start_time
        last_pane_output = (
            initial_pane_output  # Use initial output as the starting point
        )

        # When prev command is still running, and we are trying to send a new command
        if (
            self.prev_status
            in {
                BashCommandStatus.HARD_TIMEOUT,
                BashCommandStatus.NO_CHANGE_TIMEOUT,
            }
            and not last_pane_output.rstrip().endswith(
                CMD_OUTPUT_PS1_END.rstrip()
            )  # prev command is not completed
            and not is_input
            and command != ''  # not input and not empty command
        ):
            _ps1_matches = CmdOutputMetadata.matches_ps1_metadata(last_pane_output)
            # Use initial_ps1_matches if _ps1_matches is empty, otherwise use _ps1_matches
            # This handles the case where the prompt might be scrolled off screen but existed before
            current_matches_for_output = (
                _ps1_matches if _ps1_matches else initial_ps1_matches
            )
            raw_command_output = self._combine_outputs_between_matches(
                last_pane_output, current_matches_for_output
            )
            metadata = CmdOutputMetadata()  # No metadata available
            metadata.suffix = (
                f'\n[Your command "{command}" is NOT executed. '
                'The previous command is still running - You CANNOT send new commands until the previous command is completed. '
                'By setting `is_input` to `true`, you can interact with the current process: '
                f'{TIMEOUT_MESSAGE_TEMPLATE}]'
            )
            logger.debug(f'PREVIOUS COMMAND OUTPUT: {raw_command_output}')
            command_output = self._get_command_output(
                command,
                raw_command_output,
                metadata,
                continue_prefix='[Below is the output of the previous command.]\n',
            )
            return CmdOutputObservation(
                command=command,
                content=command_output,
                metadata=metadata,
                hidden=getattr(action, 'hidden', False),
            )

        # Send actual command/inputs to the pane
        if command != '' and self.pane:
            is_special_key = self._is_special_key(command)
            if is_input:
                logger.debug(f'SENDING INPUT TO RUNNING PROCESS: {command!r}')
                self.pane.send_keys(
                    command,
                    enter=not is_special_key,
                )
            else:
                # convert command to raw string
                command = escape_bash_special_chars(command)
                logger.debug(f'SENDING COMMAND: {command!r}')
                self.pane.send_keys(
                    command,
                    enter=not is_special_key,
                )

        # Loop until the command completes or times out
        while should_continue():
            _start_time = time.time()
            logger.debug(f'GETTING PANE CONTENT at {_start_time}')
            cur_pane_output = self._get_pane_content()
            logger.debug(
                f'PANE CONTENT GOT after {time.time() - _start_time:.2f} seconds'
            )
            cur_pane_lines = cur_pane_output.split('\n')
            if len(cur_pane_lines) <= 20:
                logger.debug('PANE_CONTENT: {cur_pane_output}')
            else:
                logger.debug(f'BEGIN OF PANE CONTENT: {cur_pane_lines[:10]}')
                logger.debug(f'END OF PANE CONTENT: {cur_pane_lines[-10:]}')
            ps1_matches = CmdOutputMetadata.matches_ps1_metadata(cur_pane_output)
            current_ps1_count = len(ps1_matches)

            if cur_pane_output != last_pane_output:
                last_pane_output = cur_pane_output
                last_change_time = time.time()
                logger.debug(f'CONTENT UPDATED DETECTED at {last_change_time}')

            # 1) Execution completed:
            # Condition 1: A new prompt has appeared since the command started.
            # Condition 2: The prompt count hasn't increased (potentially because the initial one scrolled off),
            # BUT the *current* visible pane ends with a prompt, indicating completion.
            if (
                current_ps1_count > initial_ps1_count
                or cur_pane_output.rstrip().endswith(CMD_OUTPUT_PS1_END.rstrip())
            ):
                return self._handle_completed_command(
                    command,
                    pane_content=cur_pane_output,
                    ps1_matches=ps1_matches,
                    hidden=getattr(action, 'hidden', False),
                )

            # Timeout checks should only trigger if a new prompt hasn't appeared yet.

            # 2) Execution timed out since there's no change in output
            # for a while (self.NO_CHANGE_TIMEOUT_SECONDS)
            # We ignore this if the command is *blocking*
            time_since_last_change = time.time() - last_change_time
            logger.debug(
                f'CHECKING NO CHANGE TIMEOUT ({self.NO_CHANGE_TIMEOUT_SECONDS}s): elapsed {time_since_last_change}. Action blocking: {action.blocking}'
            )
            if (
                not action.blocking
                and time_since_last_change >= self.NO_CHANGE_TIMEOUT_SECONDS
            ):
                return self._handle_nochange_timeout_command(
                    command,
                    pane_content=cur_pane_output,
                    ps1_matches=ps1_matches,
                )

            # 3) Execution timed out due to hard timeout
            elapsed_time = time.time() - start_time
            logger.debug(
                f'CHECKING HARD TIMEOUT ({action.timeout}s): elapsed {elapsed_time:.2f}'
            )
            if action.timeout and elapsed_time >= action.timeout:
                logger.debug('Hard timeout triggered.')
                return self._handle_hard_timeout_command(
                    command,
                    pane_content=cur_pane_output,
                    ps1_matches=ps1_matches,
                    timeout=action.timeout,
                )

            logger.debug(f'SLEEPING for {self.POLL_INTERVAL} seconds for next poll')
            time.sleep(self.POLL_INTERVAL)
        raise RuntimeError('Bash session was likely interrupted...')