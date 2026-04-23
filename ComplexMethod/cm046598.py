def export_base_model(
        self,
        save_directory: str,
        push_to_hub: bool = False,
        repo_id: Optional[str] = None,
        hf_token: Optional[str] = None,
        private: bool = False,
        base_model_id: Optional[str] = None,
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Export base model (for non-PEFT models).

        Returns:
            Tuple of (success, message, output_path). output_path is the
            resolved absolute on-disk directory of the saved model when
            ``save_directory`` was set, else None.
        """
        if not self.current_model or not self.current_tokenizer:
            return False, "No model loaded. Please select a checkpoint first.", None

        if self.is_peft:
            return (
                False,
                "This is a PEFT model. Use 'Merged Model' export type instead.",
                None,
            )

        output_path: Optional[str] = None
        try:
            # Save locally if requested
            if save_directory:
                save_directory = str(resolve_export_dir(save_directory))
                logger.info(f"Saving base model locally to: {save_directory}")
                ensure_dir(Path(save_directory))

                self.current_model.save_pretrained(save_directory)
                self.current_tokenizer.save_pretrained(save_directory)

                # Write export metadata so the Chat page can identify the base model
                self._write_export_metadata(save_directory)
                logger.info(f"Model saved successfully to {save_directory}")
                output_path = str(Path(save_directory).resolve())

            # Push to hub if requested
            if push_to_hub:
                if not repo_id or not hf_token:
                    return (
                        False,
                        "Repository ID and Hugging Face token required for Hub upload",
                        None,
                    )

                logger.info(f"Pushing base model to Hub: {repo_id}")

                # Get base model name from request or model config
                base_model = (
                    base_model_id
                    or self.current_model.config._name_or_path
                    or "unknown"
                )

                # Create repo
                hf_api = HfApi(token = hf_token)
                repo_id = PushToHubMixin._create_repo(
                    PushToHubMixin,
                    repo_id = repo_id,
                    private = private,
                    token = hf_token,
                )
                username = repo_id.split("/")[0]

                # Create and push model card
                content = MODEL_CARD.format(
                    username = username,
                    base_model = base_model,
                    model_type = self.current_model.config.model_type,
                    method = "",
                    extra = "unsloth",
                )
                card = ModelCard(content)
                card.push_to_hub(
                    repo_id, token = hf_token, commit_message = "Unsloth Model Card"
                )

                # Upload model files
                if save_directory:
                    hf_api.upload_folder(
                        folder_path = save_directory, repo_id = repo_id, repo_type = "model"
                    )
                    logger.info(f"Model pushed successfully to {repo_id}")
                else:
                    return False, "Local save directory required for Hub upload", None

            return True, "Model exported successfully", output_path

        except Exception as e:
            logger.error(f"Error exporting base model: {e}")
            import traceback

            logger.error(traceback.format_exc())
            return False, f"Export failed: {str(e)}", None