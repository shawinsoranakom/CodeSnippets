async def build_kb_info(self) -> Data:
        """Main ingestion routine → returns a dict with KB metadata."""
        # Check if we're in Astra cloud environment and raise an error if we are.
        raise_error_if_astra_cloud_disable_component(astra_error_msg)
        try:
            input_value = self.input_df[0] if isinstance(self.input_df, list) else self.input_df
            df_source: DataFrame = convert_to_dataframe(input_value, auto_parse=False)

            # Validate column configuration (using Structured Output patterns)
            config_list = self._validate_column_config(df_source)
            column_metadata = self._build_column_metadata(config_list, df_source)

            # Read the embedding info from the knowledge base folder
            kb_path = await self._kb_path()
            if not kb_path:
                msg = "Knowledge base path is not set. Please create a new knowledge base first."
                raise ValueError(msg)
            metadata_path = kb_path / "embedding_metadata.json"
            api_key = None
            model_selection = None

            # Read stored metadata
            if metadata_path.exists():
                settings_service = get_settings_service()
                stored_metadata = json.loads(metadata_path.read_text())

                # Prefer stored model_selection dict (new format)
                model_selection = stored_metadata.get("model_selection")
                if model_selection:
                    model_selection = [model_selection] if isinstance(model_selection, dict) else model_selection
                else:
                    # Backward compat: reconstruct from old string-based metadata
                    embedding_model_name = stored_metadata.get("embedding_model")
                    embedding_provider = stored_metadata.get("embedding_provider", "Unknown")
                    if embedding_model_name:
                        # Look up full model info from available options
                        try:
                            all_options = get_embedding_model_options(user_id=self.user_id)
                            match = next(
                                (o for o in all_options if o.get("name") == embedding_model_name),
                                None,
                            )
                            if match:
                                model_selection = [match]
                            else:
                                self.log(
                                    f"Embedding model '{embedding_model_name}' (provider: {embedding_provider}) "
                                    "from stored metadata is no longer available in the model registry. "
                                    "Please re-create this knowledge base with a supported embedding model."
                                )
                                msg = (
                                    f"Embedding model '{embedding_model_name}' is no longer recognized. "
                                    "The knowledge base was created with an older format and the model "
                                    "is not available in the current registry. "
                                    "Please re-create the knowledge base with a supported embedding model."
                                )
                                raise ValueError(msg)
                        except ValueError:
                            raise
                        except Exception:  # noqa: BLE001
                            self.log(
                                f"Failed to look up embedding model '{embedding_model_name}' in registry. "
                                "Please re-create this knowledge base with a supported embedding model."
                            )
                            msg = (
                                f"Could not look up embedding model '{embedding_model_name}' "
                                f"(provider: {embedding_provider}). "
                                "Please re-create the knowledge base with a supported embedding model."
                            )
                            raise ValueError(msg)  # noqa: B904

                # Decrypt stored API key
                encrypted_key = stored_metadata.get("api_key")
                if encrypted_key:
                    try:
                        api_key = decrypt_api_key(encrypted_key, settings_service)
                    except (InvalidToken, TypeError, ValueError) as e:
                        self.log(f"Could not decrypt API key. Please provide it manually. Error: {e}")

            # Check if a custom API key was provided
            if self.api_key:
                api_key = self.api_key
                if model_selection:
                    self._save_embedding_metadata(
                        kb_path=kb_path,
                        model_selection=model_selection,
                        api_key=api_key,
                    )

            if not model_selection:
                msg = "No embedding model configuration found. Please create the knowledge base first."
                raise ValueError(msg)

            # Build the embedding function via the shared utility
            embedding_function = get_embeddings(
                model=model_selection,
                user_id=self.user_id,
                api_key=api_key,
                chunk_size=self.chunk_size,
            )

            # Create vector store following Local DB component pattern
            chroma = await self._create_vector_store(df_source, config_list, embedding_function=embedding_function)

            # Save KB files (using File Component storage patterns)
            self._save_kb_files(kb_path, config_list)

            # Update embedding_metadata.json with accurate text metrics
            # so the KB modal and API show correct chunks/words/characters
            self._update_metadata_metrics(kb_path, chroma)

            # Build metadata response
            meta: dict[str, Any] = {
                "kb_id": str(uuid.uuid4()),
                "kb_name": self.knowledge_base,
                "rows": len(df_source),
                "column_metadata": column_metadata,
                "path": str(kb_path),
                "config_columns": len(config_list),
                "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            }

            # Set status message
            self.status = f"✅ KB **{self.knowledge_base}** saved · {len(df_source)} chunks."

            return Data(data=meta)

        except (OSError, ValueError, RuntimeError, KeyError) as e:
            msg = f"Error during KB ingestion: {e}"
            raise RuntimeError(msg) from e