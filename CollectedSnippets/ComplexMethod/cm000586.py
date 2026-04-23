async def _execute(self, input_data: BlockInput, **kwargs) -> BlockOutput:
        # Check for review requirement only if running within a graph execution context
        # Direct block execution (e.g., from chat) skips the review process
        has_graph_context = all(
            key in kwargs
            for key in (
                "node_exec_id",
                "graph_exec_id",
                "graph_id",
                "execution_context",
            )
        )
        if has_graph_context:
            should_pause, input_data = await self.is_block_exec_need_review(
                input_data, **kwargs
            )
            if should_pause:
                return

        # Validate the input data (original or reviewer-modified) once.
        # In dry-run mode, credential fields may contain sentinel None values
        # that would fail JSON schema required checks.  We still validate the
        # non-credential fields so blocks that execute for real during dry-run
        # (e.g. AgentExecutorBlock) get proper input validation.
        is_dry_run = getattr(kwargs.get("execution_context"), "dry_run", False)
        if is_dry_run:
            # Credential fields may be absent (LLM-built agents often skip
            # wiring them) or nullified earlier in the pipeline. Validate
            # the non-credential inputs against a schema with those fields
            # excluded — stripping only the data while keeping them in the
            # ``required`` list would falsely report ``'credentials' is a
            # required property``.
            cred_field_names = set(self.input_schema.get_credentials_fields().keys())
            if error := self.input_schema.validate_data(
                input_data, exclude_fields=cred_field_names
            ):
                raise BlockInputError(
                    message=f"Unable to execute block with invalid input data: {error}",
                    block_name=self.name,
                    block_id=self.id,
                )
        else:
            if error := self.input_schema.validate_data(input_data):
                raise BlockInputError(
                    message=f"Unable to execute block with invalid input data: {error}",
                    block_name=self.name,
                    block_id=self.id,
                )

        # Use the validated input data
        async for output_name, output_data in self.run(
            self.input_schema(**{k: v for k, v in input_data.items() if v is not None}),
            **kwargs,
        ):
            if output_name == "error":
                raise BlockExecutionError(
                    message=output_data, block_name=self.name, block_id=self.id
                )
            if self.block_type == BlockType.STANDARD and (
                error := self.output_schema.validate_field(output_name, output_data)
            ):
                raise BlockOutputError(
                    message=f"Block produced an invalid output data: {error}",
                    block_name=self.name,
                    block_id=self.id,
                )
            yield output_name, output_data