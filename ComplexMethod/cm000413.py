def register_provider_costs_for_block(block_class: Type[Block]) -> None:
    """
    Register provider base costs for a specific block in BLOCK_COSTS.

    This function checks if the block uses credentials from a provider that has
    base costs defined, and automatically registers those costs for the block.

    Args:
        block_class: The block class to register costs for
    """
    # Skip if block already has custom costs defined
    if block_class in BLOCK_COSTS:
        logger.debug(
            f"Block {block_class.__name__} already has costs defined, skipping provider costs"
        )
        return

    # Get the block's input schema
    # We need to instantiate the block to get its input schema
    try:
        block_instance = block_class()
        input_schema = block_instance.input_schema
    except Exception as e:
        logger.debug(f"Block {block_class.__name__} cannot be instantiated: {e}")
        return

    # Look for credentials fields
    # The cost system works of filtering on credentials fields,
    # without credentials fields, we can not apply costs
    # TODO: Improve cost system to allow for costs witout a provider
    credentials_fields = input_schema.get_credentials_fields()
    if not credentials_fields:
        logger.debug(f"Block {block_class.__name__} has no credentials fields")
        return

    # Get provider information from credentials fields
    for field_name, field_info in credentials_fields.items():
        # Get the field schema to extract provider information
        field_schema = input_schema.get_field_schema(field_name)

        # Extract provider names from json_schema_extra
        providers = field_schema.get("credentials_provider", [])
        if not providers:
            continue

        # For each provider, check if it has base costs
        block_costs: List[BlockCost] = []
        for provider_name in providers:
            provider = AutoRegistry.get_provider(provider_name)
            if not provider:
                logger.debug(f"Provider {provider_name} not found in registry")
                continue

            # Add provider's base costs to the block
            if provider.base_costs:
                logger.debug(
                    f"Registering {len(provider.base_costs)} base costs from provider {provider_name} for block {block_class.__name__}"
                )
                block_costs.extend(provider.base_costs)

        # Register costs if any were found
        if block_costs:
            BLOCK_COSTS[block_class] = block_costs
            logger.debug(
                f"Registered {len(block_costs)} total costs for block {block_class.__name__}"
            )