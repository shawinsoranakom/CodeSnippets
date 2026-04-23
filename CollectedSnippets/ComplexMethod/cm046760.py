def scan_exported_models(
    exports_dir: str = str(exports_root()),
) -> List[Tuple[str, str, str, Optional[str]]]:
    """
    Scan exports folder for exported models (merged, LoRA, GGUF).

    Supports two directory layouts:
      - Two-level: {run}/{checkpoint}/  (merged & LoRA exports)
      - Flat:      {name}-finetune-gguf/  (GGUF exports)

    Returns:
        List of tuples: [(display_name, model_path, export_type, base_model), ...]
        export_type: "lora" | "merged" | "gguf"
    """
    results = []
    exports_path = resolve_export_dir(exports_dir)

    if not exports_path.exists():
        return results

    try:
        for run_dir in exports_path.iterdir():
            if not run_dir.is_dir():
                continue

            # Check for flat GGUF export (e.g. exports/gemma-3-4b-it-finetune-gguf/)
            # Filter out mmproj (vision projection) files — they aren't loadable as main models
            gguf_files = [
                f for f in _iter_gguf_files(run_dir) if not _is_mmproj(f.name)
            ]
            if gguf_files:
                base_model = None
                export_meta = run_dir / "export_metadata.json"
                try:
                    if export_meta.exists():
                        meta = json.loads(export_meta.read_text())
                        base_model = meta.get("base_model")
                except Exception:
                    pass

                display_name = run_dir.name
                model_path = str(gguf_files[0])  # path to the .gguf file
                results.append((display_name, model_path, "gguf", base_model))
                logger.debug(f"Found GGUF export: {display_name}")
                continue

            # Two-level: {run}/{checkpoint}/
            for checkpoint_dir in run_dir.iterdir():
                if not checkpoint_dir.is_dir():
                    continue

                adapter_config = checkpoint_dir / "adapter_config.json"
                config_file = checkpoint_dir / "config.json"
                has_weights = any(checkpoint_dir.glob("*.safetensors")) or any(
                    checkpoint_dir.glob("*.bin")
                )
                has_gguf = any(_iter_gguf_files(checkpoint_dir))

                base_model = None
                export_type = None

                if adapter_config.exists():
                    export_type = "lora"
                    try:
                        cfg = json.loads(adapter_config.read_text())
                        base_model = cfg.get("base_model_name_or_path")
                    except Exception:
                        pass
                elif config_file.exists() and has_weights:
                    export_type = "merged"
                    export_meta = checkpoint_dir / "export_metadata.json"
                    try:
                        if export_meta.exists():
                            meta = json.loads(export_meta.read_text())
                            base_model = meta.get("base_model")
                    except Exception:
                        pass
                elif has_gguf:
                    export_type = "gguf"
                    gguf_list = list(_iter_gguf_files(checkpoint_dir))
                    # Check checkpoint_dir first, then fall back to parent run_dir
                    # (export.py writes metadata to the top-level export directory)
                    for meta_dir in (checkpoint_dir, run_dir):
                        export_meta = meta_dir / "export_metadata.json"
                        try:
                            if export_meta.exists():
                                meta = json.loads(export_meta.read_text())
                                base_model = meta.get("base_model")
                                if base_model:
                                    break
                        except Exception:
                            pass

                    display_name = f"{run_dir.name} / {checkpoint_dir.name}"
                    model_path = str(gguf_list[0]) if gguf_list else str(checkpoint_dir)
                    results.append((display_name, model_path, export_type, base_model))
                    logger.debug(f"Found GGUF export: {display_name}")
                    continue
                else:
                    continue

                # Fallback: read base model from the original training run's
                # adapter_config.json in ./outputs/{run_name}/
                if not base_model:
                    outputs_adapter_cfg = (
                        resolve_output_dir(run_dir.name) / "adapter_config.json"
                    )
                    try:
                        if outputs_adapter_cfg.exists():
                            cfg = json.loads(outputs_adapter_cfg.read_text())
                            base_model = cfg.get("base_model_name_or_path")
                    except Exception:
                        pass

                display_name = f"{run_dir.name} / {checkpoint_dir.name}"
                model_path = str(checkpoint_dir)
                results.append((display_name, model_path, export_type, base_model))
                logger.debug(f"Found exported model: {display_name} ({export_type})")

        results.sort(key = lambda x: Path(x[1]).stat().st_mtime, reverse = True)
        logger.info(f"Found {len(results)} exported models in {exports_dir}")
        return results

    except Exception as e:
        logger.error(f"Error scanning exports folder: {e}")
        return []