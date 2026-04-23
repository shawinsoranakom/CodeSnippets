def export_gguf(
        self,
        save_directory: str,
        quantization_method: str = "Q4_K_M",
        push_to_hub: bool = False,
        repo_id: Optional[str] = None,
        hf_token: Optional[str] = None,
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Export model in GGUF format.

        Args:
            save_directory: Local directory to save model
            quantization_method: GGUF quantization method (e.g., "Q4_K_M")
            push_to_hub: Whether to push to Hugging Face Hub
            repo_id: Hub repository ID
            hf_token: Hugging Face token

        Returns:
            Tuple of (success, message, output_path). output_path is the
            resolved absolute on-disk directory containing the .gguf
            files when ``save_directory`` was set, else None.
        """
        if not self.current_model or not self.current_tokenizer:
            return False, "No model loaded. Please select a checkpoint first.", None

        output_path: Optional[str] = None
        try:
            # Convert quantization method to lowercase for unsloth
            quant_method = quantization_method.lower()

            # Save locally if requested
            if save_directory:
                save_directory = str(resolve_export_dir(save_directory))
                # Resolve to absolute path so unsloth's relative-path internals
                # (check_llama_cpp, use_local_gguf, _download_convert_hf_to_gguf)
                # all resolve against the repo root cwd, NOT the export directory.
                abs_save_dir = os.path.abspath(save_directory)
                logger.info(f"Saving GGUF model locally to: {abs_save_dir}")

                # Create the directory if it doesn't exist
                ensure_dir(Path(abs_save_dir))

                # On WSL, patch out sudo check before llama.cpp build
                _apply_wsl_sudo_patch()

                # Snapshot existing .gguf files in cwd before conversion.
                # unsloth's convert_to_gguf writes output files relative to
                # cwd (repo root), so we diff afterwards and relocate them.
                cwd = os.getcwd()
                pre_existing_ggufs = set(glob.glob(os.path.join(cwd, "*.gguf")))

                # Pass absolute path — no os.chdir needed.
                # unsloth saves intermediate HF model files into model_save_path.
                # unsloth-zoo's check_llama_cpp() uses ~/.unsloth/llama.cpp by default.
                model_save_path = os.path.join(abs_save_dir, "model")
                self.current_model.save_pretrained_gguf(
                    model_save_path,
                    self.current_tokenizer,
                    quantization_method = quant_method,
                )

                # Relocate GGUF artifacts into the export directory.
                # convert_to_gguf writes .gguf files to cwd (repo root)
                # because --outfile is a relative path like "model.Q4_K_M.gguf".
                new_ggufs = (
                    set(glob.glob(os.path.join(cwd, "*.gguf"))) - pre_existing_ggufs
                )
                for src in sorted(new_ggufs):
                    dest = os.path.join(abs_save_dir, os.path.basename(src))
                    shutil.move(src, dest)
                    logger.info(
                        f"Relocated GGUF: {os.path.basename(src)} → {abs_save_dir}/"
                    )

                # Flatten any .gguf files from subdirectories into abs_save_dir.
                # save_pretrained_gguf may create subdirs (e.g. model_gguf/)
                # with a name different from model_save_path.
                for sub in list(Path(abs_save_dir).iterdir()):
                    if not sub.is_dir():
                        continue
                    for src in sub.glob("*.gguf"):
                        dest = os.path.join(abs_save_dir, src.name)
                        shutil.move(str(src), dest)
                        logger.info(f"Relocated GGUF: {src.name} → {abs_save_dir}/")
                    # Clean up the subdirectory (intermediate HF files, etc.)
                    shutil.rmtree(str(sub), ignore_errors = True)
                    logger.info(f"Cleaned up subdirectory: {sub.name}")

                # For non-PEFT models, save_pretrained_gguf redirects to the
                # checkpoint path, leaving a *_gguf directory in outputs/.
                # Relocate any GGUFs from there and clean it up.
                if self.current_checkpoint:
                    ckpt = Path(self.current_checkpoint)
                    gguf_dir = ckpt.parent / f"{ckpt.name}_gguf"
                    if gguf_dir.is_dir():
                        for src in gguf_dir.glob("*.gguf"):
                            dest = os.path.join(abs_save_dir, src.name)
                            shutil.move(str(src), dest)
                            logger.info(f"Relocated GGUF: {src.name} → {abs_save_dir}/")
                        # Also relocate Ollama Modelfile if present
                        modelfile = gguf_dir / "Modelfile"
                        if modelfile.is_file():
                            shutil.move(
                                str(modelfile), os.path.join(abs_save_dir, "Modelfile")
                            )
                            logger.info(f"Relocated Modelfile → {abs_save_dir}/")
                        shutil.rmtree(str(gguf_dir), ignore_errors = True)
                        logger.info(f"Cleaned up intermediate GGUF dir: {gguf_dir}")

                # Write export metadata so the Chat page can identify the base model
                self._write_export_metadata(abs_save_dir)

                # Log final file locations (after relocation) so it's clear
                # where the GGUF files actually ended up.
                final_ggufs = sorted(glob.glob(os.path.join(abs_save_dir, "*.gguf")))
                logger.info(
                    "GGUF export complete. Final files in %s:\n  %s",
                    abs_save_dir,
                    "\n  ".join(os.path.basename(f) for f in final_ggufs) or "(none)",
                )
                output_path = str(Path(abs_save_dir).resolve())

            # Push to hub if requested
            if push_to_hub:
                if not repo_id or not hf_token:
                    return (
                        False,
                        "Repository ID and Hugging Face token required for Hub upload",
                        None,
                    )

                logger.info(f"Pushing GGUF model to Hub: {repo_id}")

                self.current_model.push_to_hub_gguf(
                    repo_id,
                    self.current_tokenizer,
                    quantization_method = quant_method,
                    token = hf_token,
                )
                logger.info(f"GGUF model pushed successfully to {repo_id}")

            return (
                True,
                f"GGUF model exported successfully ({quantization_method})",
                output_path,
            )

        except Exception as e:
            logger.error(f"Error exporting GGUF model: {e}")
            import traceback

            logger.error(traceback.format_exc())
            return False, f"GGUF export failed: {str(e)}", None