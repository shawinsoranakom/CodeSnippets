async def run_batch(self) -> DataFrame:
        """Process each row in df[column_name] with the language model asynchronously."""
        # Check if model is already an instance (for testing) or needs to be instantiated
        if isinstance(self.model, list):
            model = get_llm(
                model=self.model,
                user_id=self.user_id,
                api_key=self.api_key,
                watsonx_url=getattr(self, "base_url_ibm_watsonx", None),
                watsonx_project_id=getattr(self, "project_id", None),
            )
        else:
            # Model is already an instance (typically in tests)
            model = self.model

        system_msg = self.system_message or ""
        df: DataFrame = self.df
        col_name = self.column_name or ""

        # Validate inputs first
        if not isinstance(df, DataFrame):
            msg = f"Expected DataFrame input, got {type(df)}"
            raise TypeError(msg)

        if col_name and col_name not in df.columns:
            msg = f"Column '{col_name}' not found in the DataFrame. Available columns: {', '.join(df.columns)}"
            raise ValueError(msg)

        try:
            # Determine text input for each row
            if col_name:
                user_texts = df[col_name].astype(str).tolist()
            else:
                user_texts = [
                    self._format_row_as_toml(cast("dict[str, Any]", row)) for row in df.to_dict(orient="records")
                ]

            total_rows = len(user_texts)
            await logger.ainfo(f"Processing {total_rows} rows with batch run")

            # Prepare the batch of conversations
            conversations = [
                [{"role": "system", "content": system_msg}, {"role": "user", "content": text}]
                if system_msg
                else [{"role": "user", "content": text}]
                for text in user_texts
            ]

            # Configure the model with project info and callbacks
            # Some models (e.g., ChatWatsonx) may have serialization issues with with_config()
            # due to SecretStr or other non-serializable attributes
            try:
                model = model.with_config(
                    {
                        "run_name": self.display_name,
                        "project_name": self.get_project_name(),
                        "callbacks": self.get_langchain_callbacks(),
                    }
                )
            except (TypeError, ValueError, AttributeError) as e:
                # Log warning and continue without configuration
                await logger.awarning(
                    f"Could not configure model with callbacks and project info: {e!s}. "
                    "Proceeding with batch processing without configuration."
                )
            # Process batches and track progress
            responses_with_idx = list(
                zip(
                    range(len(conversations)),
                    await model.abatch(list(conversations)),
                    strict=True,
                )
            )

            # Sort by index to maintain order
            responses_with_idx.sort(key=lambda x: x[0])

            # Build the final data with enhanced metadata
            rows: list[dict[str, Any]] = []
            for idx, (original_row, response) in enumerate(
                zip(df.to_dict(orient="records"), responses_with_idx, strict=False)
            ):
                response_msg = response[1]
                self._token_usage = accumulate_usage(self._token_usage, extract_usage_from_message(response_msg))
                response_text = response_msg.content if hasattr(response_msg, "content") else str(response_msg)
                row = self._create_base_row(
                    cast("dict[str, Any]", original_row), model_response=response_text, batch_index=idx
                )
                self._add_metadata(row, success=True, system_msg=system_msg)
                rows.append(row)

                # Log progress
                if (idx + 1) % max(1, total_rows // 10) == 0:
                    await logger.ainfo(f"Processed {idx + 1}/{total_rows} rows")

            await logger.ainfo("Batch processing completed successfully")
            return DataFrame(rows)

        except (KeyError, AttributeError) as e:
            # Handle data structure and attribute access errors
            await logger.aerror(f"Data processing error: {e!s}")
            error_row = self._create_base_row(dict.fromkeys(df.columns, ""), model_response="", batch_index=-1)
            self._add_metadata(error_row, success=False, error=str(e))
            return DataFrame([error_row])