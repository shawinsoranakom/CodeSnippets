def __init__(self, chains: Sequence[Chain], names: list[str] | None = None):
        """Initialize the ModelLaboratory with chains to experiment with.

        Args:
            chains: A sequence of chains to experiment with.
                Each chain must have exactly one input and one output variable.
            names: Optional list of names corresponding to each chain.
                If provided, its length must match the number of chains.


        Raises:
            ValueError: If any chain is not an instance of `Chain`.
            ValueError: If a chain does not have exactly one input variable.
            ValueError: If a chain does not have exactly one output variable.
            ValueError: If the length of `names` does not match the number of chains.
        """
        for chain in chains:
            if not isinstance(chain, Chain):
                msg = (  # type: ignore[unreachable]
                    "ModelLaboratory should now be initialized with Chains. "
                    "If you want to initialize with LLMs, use the `from_llms` method "
                    "instead (`ModelLaboratory.from_llms(...)`)"
                )
                raise ValueError(msg)  # noqa: TRY004
            if len(chain.input_keys) != 1:
                msg = (
                    "Currently only support chains with one input variable, "
                    f"got {chain.input_keys}"
                )
                raise ValueError(msg)
            if len(chain.output_keys) != 1:
                msg = (
                    "Currently only support chains with one output variable, "
                    f"got {chain.output_keys}"
                )
        if names is not None and len(names) != len(chains):
            msg = "Length of chains does not match length of names."
            raise ValueError(msg)
        self.chains = chains
        chain_range = [str(i) for i in range(len(self.chains))]
        self.chain_colors = get_color_mapping(chain_range)
        self.names = names