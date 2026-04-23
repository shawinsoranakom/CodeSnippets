async def aReduce(self) -> DataFrame:  # noqa: N802
        """Aggregate input data using LLM-based semantic analysis.

        Returns:
            DataFrame containing the aggregated results following the output schema.
        """
        try:
            from agentics import AG
            from agentics.core.atype import create_pydantic_model
        except ImportError as e:
            raise ImportError(ERROR_AGENTICS_NOT_INSTALLED) from e

        llm = prepare_llm_from_component(self)

        if self.source and self.schema != []:
            source = AG.from_dataframe(DataFrame(self.source))

            schema_fields = build_schema_fields(self.schema)
            atype = create_pydantic_model(schema_fields, name="Target")
            if self.return_multiple_instances:
                final_atype = create_model("ListOfTarget", items=(list[atype], ...))  # type: ignore[valid-type]
            else:
                final_atype = atype

            target = AG(
                atype=final_atype,
                transduction_type=TRANSDUCTION_AREDUCE,
                instructions=self.instructions
                if not self.return_multiple_instances
                else "\nGenerate a list of instances of the target type following those instructions : ."
                + self.instructions,
                llm=llm,
                areduce_batch_size=100,
            )

            output = await (target << source)
            if self.return_multiple_instances:
                appended_states = [item_state for state in output for item_state in state.items]
                output = AG(atype=atype, states=appended_states)

            return DataFrame(output.to_dataframe().to_dict(orient="records"))
        raise ValueError(ERROR_INPUT_SCHEMA_REQUIRED)