async def aMap(self) -> DataFrame:  # noqa: N802
        """Transform input data row-by-row using LLM-based semantic processing.

        Returns:
            DataFrame with transformed data following the output schema.
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
                transduction_type=TRANSDUCTION_AMAP,
                llm=llm,
            )
            if "{" in self.instructions:
                source.prompt_template = self.instructions
            else:
                source.instructions += self.instructions

            output = await (target << source)
            if self.return_multiple_instances:
                appended_states = [item_state for state in output for item_state in state.items]
                output = AG(atype=atype, states=appended_states)

            elif self.append_to_input_columns:
                output_field_names = set(output.atype.model_fields.keys())
                source_field_names = set(source.atype.model_fields.keys())
                overlapping = source_field_names & output_field_names
                if overlapping:
                    non_overlapping = source_field_names - overlapping
                    deduplicated_atype = source.subset_atype(non_overlapping)
                    source = source.rebind_atype(deduplicated_atype)
                output = source.merge_states(output)

            return DataFrame(output.to_dataframe().to_dict(orient="records"))
        raise ValueError(ERROR_INPUT_SCHEMA_REQUIRED)