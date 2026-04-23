def export_merged_model(
        self,
        save_directory: str,
        format_type: str = "16-bit (FP16)",
        push_to_hub: bool = False,
        repo_id: Optional[str] = None,
        hf_token: Optional[str] = None,
        private: bool = False,
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Export merged model (for PEFT models).

        Args:
            save_directory: Local directory to save model
            format_type: "16-bit (FP16)" or "4-bit (FP4)"
            push_to_hub: Whether to push to Hugging Face Hub
            repo_id: Hub repository ID (username/model-name)
            hf_token: Hugging Face token
            private: Whether to make the repo private

        Returns:
            Tuple of (success, message, output_path). output_path is the
            resolved absolute on-disk directory of the saved model when
            ``save_directory`` was set, else None.
        """
        if not self.current_model or not self.current_tokenizer:
            return False, "No model loaded. Please select a checkpoint first.", None

        if not self.is_peft:
            return (
                False,
                "This is not a PEFT model. Use 'Export Base Model' instead.",
                None,
            )

        output_path: Optional[str] = None
        try:
            # Determine save method
            if format_type == "4-bit (FP4)":
                save_method = "merged_4bit_forced"
            elif self._audio_type == "whisper":
                # Whisper uses save_method=None for local 16-bit merged save
                save_method = None
            else:  # 16-bit (FP16)
                save_method = "merged_16bit"

            # Save locally if requested
            if save_directory:
                save_directory = str(resolve_export_dir(save_directory))
                logger.info(f"Saving merged model locally to: {save_directory}")
                ensure_dir(Path(save_directory))

                self.current_model.save_pretrained_merged(
                    save_directory, self.current_tokenizer, save_method = save_method
                )

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

                logger.info(f"Pushing merged model to Hub: {repo_id}")

                # Whisper uses save_method=None for local but "merged_16bit" for hub push
                hub_save_method = (
                    save_method if save_method is not None else "merged_16bit"
                )
                self.current_model.push_to_hub_merged(
                    repo_id,
                    self.current_tokenizer,
                    save_method = hub_save_method,
                    token = hf_token,
                    private = private,
                )
                logger.info(f"Model pushed successfully to {repo_id}")

            return True, "Model exported successfully", output_path

        except Exception as e:
            logger.error(f"Error exporting merged model: {e}")
            import traceback

            logger.error(traceback.format_exc())
            return False, f"Export failed: {str(e)}", None