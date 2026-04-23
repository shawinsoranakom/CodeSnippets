async def resolve_issue(
        self,
        reset_logger: bool = False,
    ) -> None:
        """Resolve a single issue.

        Args:
            reset_logger: Whether to reset the logger for multiprocessing.
        """
        issue = self.extract_issue()

        if self.comment_id is not None:
            if (
                self.issue_type == 'pr'
                and not issue.review_comments
                and not issue.review_threads
                and not issue.thread_comments
            ):
                raise ValueError(
                    f'Comment ID {self.comment_id} did not have a match for issue {issue.number}'
                )

            if self.issue_type == 'issue' and not issue.thread_comments:
                raise ValueError(
                    f'Comment ID {self.comment_id} did not have a match for issue {issue.number}'
                )

        # TEST METADATA
        model_name = self.app_config.get_llm_config().model.split('/')[-1]

        pathlib.Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        pathlib.Path(os.path.join(self.output_dir, 'infer_logs')).mkdir(
            parents=True, exist_ok=True
        )
        logger.info(f'Using output directory: {self.output_dir}')

        # checkout the repo
        repo_dir = os.path.join(self.output_dir, 'repo')
        if not os.path.exists(repo_dir):
            checkout_output = subprocess.check_output(
                [
                    'git',
                    'clone',
                    self.issue_handler.get_clone_url(),
                    f'{self.output_dir}/repo',
                ]
            ).decode('utf-8')
            if 'fatal' in checkout_output:
                raise RuntimeError(f'Failed to clone repository: {checkout_output}')

        # get the commit id of current repo for reproducibility
        base_commit = (
            subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=repo_dir)
            .decode('utf-8')
            .strip()
        )
        logger.info(f'Base commit: {base_commit}')

        if self.repo_instruction is None:
            # Check for .openhands_instructions file in the workspace directory
            openhands_instructions_path = os.path.join(
                repo_dir, '.openhands_instructions'
            )
            if os.path.exists(openhands_instructions_path):
                with open(openhands_instructions_path, 'r') as f:
                    self.repo_instruction = f.read()

        # OUTPUT FILE
        output_file = os.path.join(self.output_dir, 'output.jsonl')
        logger.info(f'Writing output to {output_file}')

        # Check if this issue was already processed
        if os.path.exists(output_file):
            with open(output_file, 'r') as f:
                for line in f:
                    data = ResolverOutput.model_validate_json(line)
                    if data.issue.number == self.issue_number:
                        logger.warning(
                            f'Issue {self.issue_number} was already processed. Skipping.'
                        )
                        return

        output_fp = open(output_file, 'a')

        logger.info(
            f'Resolving issue {self.issue_number} with Agent {AGENT_CLASS}, model {model_name}, max iterations {self.max_iterations}.'
        )

        try:
            # checkout to pr branch if needed
            if self.issue_type == 'pr':
                branch_to_use = issue.head_branch
                logger.info(
                    f'Checking out to PR branch {branch_to_use} for issue {issue.number}'
                )

                if not branch_to_use:
                    raise ValueError('Branch name cannot be None')

                # Fetch the branch first to ensure it exists locally
                fetch_cmd = ['git', 'fetch', 'origin', branch_to_use]
                subprocess.check_output(
                    fetch_cmd,
                    cwd=repo_dir,
                )

                # Checkout the branch
                checkout_cmd = ['git', 'checkout', branch_to_use]
                subprocess.check_output(
                    checkout_cmd,
                    cwd=repo_dir,
                )

                base_commit = (
                    subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=repo_dir)
                    .decode('utf-8')
                    .strip()
                )

            output = await self.process_issue(
                issue,
                base_commit,
                self.issue_handler,
                reset_logger,
            )
            output_fp.write(output.model_dump_json() + '\n')
            output_fp.flush()

        finally:
            output_fp.close()
            logger.info('Finished.')