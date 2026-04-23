async def process_issue(
        self,
        issue: Issue,
        base_commit: str,
        issue_handler: ServiceContextIssue | ServiceContextPR,
        reset_logger: bool = False,
    ) -> ResolverOutput:
        # Setup the logger properly, so you can run multi-processing to parallelize processing
        if reset_logger:
            log_dir = os.path.join(self.output_dir, 'infer_logs')
            reset_logger_for_multiprocessing(logger, str(issue.number), log_dir)
        else:
            logger.info(f'Starting fixing issue {issue.number}.')

        # write the repo to the workspace
        if os.path.exists(self.workspace_base):
            shutil.rmtree(self.workspace_base)
        shutil.copytree(os.path.join(self.output_dir, 'repo'), self.workspace_base)

        llm_registry = LLMRegistry(self.app_config)
        runtime = create_runtime(self.app_config, llm_registry)
        await runtime.connect()

        def on_event(evt: Event) -> None:
            logger.info(evt)

        runtime.event_stream.subscribe(
            EventStreamSubscriber.MAIN, on_event, str(uuid4())
        )

        self.initialize_runtime(runtime)

        instruction, conversation_instructions, images_urls = (
            issue_handler.get_instruction(
                issue,
                self.user_instructions_prompt_template,
                self.conversation_instructions_prompt_template,
                self.repo_instruction,
            )
        )
        # Here's how you can run the agent (similar to the `main` function) and get the final task state
        action = MessageAction(content=instruction, image_urls=images_urls)
        try:
            state: State | None = await run_controller(
                config=self.app_config,
                initial_user_action=action,
                runtime=runtime,
                fake_user_response_fn=codeact_user_response,
                conversation_instructions=conversation_instructions,
            )
            if state is None:
                raise RuntimeError('Failed to run the agent.')
        except (ValueError, RuntimeError) as e:
            error_msg = f'Agent failed with error: {str(e)}'
            logger.error(error_msg)
            state = None
            last_error: str | None = error_msg

        # Get git patch
        return_val = await self.complete_runtime(runtime, base_commit)
        git_patch = return_val['git_patch']
        logger.info(
            f'Got git diff for instance {issue.number}:\n--------\n{git_patch}\n--------'
        )

        # Serialize histories and set defaults for failed state
        if state is None:
            histories = []
            metrics = None
            success = False
            comment_success = None
            result_explanation = 'Agent failed to run'
            last_error = 'Agent failed to run or crashed'
        else:
            histories = [dataclasses.asdict(event) for event in state.history]
            metrics = state.metrics.get() if state.metrics else None
            # determine success based on the history, issue description and git patch
            success, comment_success, result_explanation = issue_handler.guess_success(
                issue, state.history, git_patch
            )

            if issue_handler.issue_type == 'pr' and comment_success:
                success_log = 'I have updated the PR and resolved some of the issues that were cited in the pull request review. Specifically, I identified the following revision requests, and all the ones that I think I successfully resolved are checked off. All the unchecked ones I was not able to resolve, so manual intervention may be required:\n'
                try:
                    explanations = json.loads(result_explanation)
                except json.JSONDecodeError:
                    logger.error(
                        f'Failed to parse result_explanation as JSON: {result_explanation}'
                    )
                    explanations = [
                        str(result_explanation)
                    ]  # Use raw string as fallback

                for success_indicator, explanation in zip(
                    comment_success, explanations
                ):
                    status = (
                        colored('[X]', 'red')
                        if success_indicator
                        else colored('[ ]', 'red')
                    )
                    bullet_point = colored('-', 'yellow')
                    success_log += f'\n{bullet_point} {status}: {explanation}'
                logger.info(success_log)
            last_error = state.last_error if state.last_error else None

        # Save the output
        output = ResolverOutput(
            issue=issue,
            issue_type=issue_handler.issue_type,
            instruction=instruction,
            base_commit=base_commit,
            git_patch=git_patch,
            history=histories,
            metrics=metrics,
            success=success,
            comment_success=comment_success,
            result_explanation=result_explanation,
            error=last_error,
        )
        return output