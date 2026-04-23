def __init__(
        self,
        id: str = "",
        description: str = "",
        contributors: list["ContributorDetails"] = [],
        categories: set[BlockCategory] | None = None,
        input_schema: Type[BlockSchemaInputType] = EmptyInputSchema,
        output_schema: Type[BlockSchemaOutputType] = EmptyOutputSchema,
        test_input: BlockInput | list[BlockInput] | None = None,
        test_output: BlockTestOutput | list[BlockTestOutput] | None = None,
        test_mock: dict[str, Any] | None = None,
        test_credentials: Optional[Credentials | dict[str, Credentials]] = None,
        disabled: bool = False,
        static_output: bool = False,
        block_type: BlockType = BlockType.STANDARD,
        webhook_config: Optional[BlockWebhookConfig | BlockManualWebhookConfig] = None,
        is_sensitive_action: bool = False,
    ):
        """
        Initialize the block with the given schema.

        Args:
            id: The unique identifier for the block, this value will be persisted in the
                DB. So it should be a unique and constant across the application run.
                Use the UUID format for the ID.
            description: The description of the block, explaining what the block does.
            contributors: The list of contributors who contributed to the block.
            input_schema: The schema, defined as a Pydantic model, for the input data.
            output_schema: The schema, defined as a Pydantic model, for the output data.
            test_input: The list or single sample input data for the block, for testing.
            test_output: The list or single expected output if the test_input is run.
            test_mock: function names on the block implementation to mock on test run.
            disabled: If the block is disabled, it will not be available for execution.
            static_output: Whether the output links of the block are static by default.
        """
        self.id = id
        self.input_schema = input_schema
        self.output_schema = output_schema
        self.test_input = test_input
        self.test_output = test_output
        self.test_mock = test_mock
        self.test_credentials = test_credentials
        self.description = description
        self.categories = categories or set()
        self.contributors = contributors or set()
        self.disabled = disabled
        self.static_output = static_output
        self.block_type = block_type
        self.webhook_config = webhook_config
        self.is_sensitive_action = is_sensitive_action
        # Read from ClassVar set by initialize_blocks()
        self.optimized_description: str | None = type(self)._optimized_description
        self.execution_stats: NodeExecutionStats = NodeExecutionStats()

        if self.webhook_config:
            if isinstance(self.webhook_config, BlockWebhookConfig):
                # Enforce presence of credentials field on auto-setup webhook blocks
                if not (cred_fields := self.input_schema.get_credentials_fields()):
                    raise TypeError(
                        "credentials field is required on auto-setup webhook blocks"
                    )
                # Disallow multiple credentials inputs on webhook blocks
                elif len(cred_fields) > 1:
                    raise ValueError(
                        "Multiple credentials inputs not supported on webhook blocks"
                    )

                self.block_type = BlockType.WEBHOOK
            else:
                self.block_type = BlockType.WEBHOOK_MANUAL

            # Enforce shape of webhook event filter, if present
            if self.webhook_config.event_filter_input:
                event_filter_field = self.input_schema.model_fields[
                    self.webhook_config.event_filter_input
                ]
                if not (
                    isinstance(event_filter_field.annotation, type)
                    and issubclass(event_filter_field.annotation, BaseModel)
                    and all(
                        field.annotation is bool
                        for field in event_filter_field.annotation.model_fields.values()
                    )
                ):
                    raise NotImplementedError(
                        f"{self.name} has an invalid webhook event selector: "
                        "field must be a BaseModel and all its fields must be boolean"
                    )

            # Enforce presence of 'payload' input
            if "payload" not in self.input_schema.model_fields:
                raise TypeError(
                    f"{self.name} is webhook-triggered but has no 'payload' input"
                )

            # Disable webhook-triggered block if webhook functionality not available
            if not app_config.platform_base_url:
                self.disabled = True