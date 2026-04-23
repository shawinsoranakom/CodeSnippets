async def aGenerate(self) -> DataFrame:  # noqa: N802
        """Generate synthetic data using LLM-based generation.

        Returns:
            DataFrame containing the generated synthetic data.
        """
        try:
            from agentics import AG
            from agentics.core.atype import create_pydantic_model
            from agentics.core.transducible_functions import generate_prototypical_instances
        except ImportError as e:
            raise ImportError(ERROR_AGENTICS_NOT_INSTALLED) from e

        llm = prepare_llm_from_component(self)

        if self.source:
            source = AG.from_dataframe(DataFrame(self.source))
            atype = source.atype
            instructions = (
                str(self.instructions) if self.instructions else "Generate similar data based on the examples provided."
            )
            instructions += "\nHere are examples to take inspiration from:\n" + str(source.states[:50])
        elif self.schema != []:
            schema_fields = build_schema_fields(self.schema)
            atype = create_pydantic_model(schema_fields, name="GeneratedData")
            instructions = (
                str(self.instructions)
                if self.instructions
                else "Generate realistic synthetic data following the provided schema."
            )
        else:
            msg = "Synthetic data generation requires either a sample DataFrame or schema definition (but not both)."
            raise ValueError(msg)

        output_states = await generate_prototypical_instances(
            atype,
            n_instances=self.batch_size,
            llm=llm,
            instructions=instructions,
        )
        # Ensure output_states is a list, not None
        if output_states is None:
            output_states = []

        if self.source:
            output_states = source.states + output_states

        output = AG(atype=atype, states=output_states)

        return DataFrame(output.to_dataframe().to_dict(orient="records"))