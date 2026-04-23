def export_lora_adapter(
        self,
        save_directory: str,
        push_to_hub: bool = False,
        repo_id: Optional[str] = None,
        hf_token: Optional[str] = None,
        private: bool = False,
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Export LoRA adapter only (not merged).

        Returns:
            Tuple of (success, message, output_path). output_path is the
            resolved absolute on-disk directory of the saved adapter
            when ``save_directory`` was set, else None.
        """
        if not self.current_model or not self.current_tokenizer:
            return False, "No model loaded. Please select a checkpoint first.", None

        if not self.is_peft:
            return False, "This is not a PEFT model. No adapter to export.", None

        output_path: Optional[str] = None
        try:
            # Save locally if requested
            if save_directory:
                save_directory = str(resolve_export_dir(save_directory))
                logger.info(f"Saving LoRA adapter locally to: {save_directory}")
                ensure_dir(Path(save_directory))

                self.current_model.save_pretrained(save_directory)
                self.current_tokenizer.save_pretrained(save_directory)
                logger.info(f"Adapter saved successfully to {save_directory}")
                output_path = str(Path(save_directory).resolve())

            # Push to hub if requested
            if push_to_hub:
                if not repo_id or not hf_token:
                    return (
                        False,
                        "Repository ID and Hugging Face token required for Hub upload",
                        None,
                    )

                logger.info(f"Pushing LoRA adapter to Hub: {repo_id}")

                self.current_model.push_to_hub(repo_id, token = hf_token, private = private)
                self.current_tokenizer.push_to_hub(
                    repo_id, token = hf_token, private = private
                )
                logger.info(f"Adapter pushed successfully to {repo_id}")

            return True, "LoRA adapter exported successfully", output_path

        except Exception as e:
            logger.error(f"Error exporting LoRA adapter: {e}")
            import traceback

            logger.error(traceback.format_exc())
            return False, f"Adapter export failed: {str(e)}", None