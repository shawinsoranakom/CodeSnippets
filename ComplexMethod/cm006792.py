def docling_worker(
    *,
    file_paths: list[str],
    queue,
    pipeline: str,
    ocr_engine: str,
    do_picture_classification: bool,
    pic_desc_config: dict | None,
    pic_desc_prompt: str,
):
    """Worker function for processing files with Docling using threading.

    This function now uses a globally cached DocumentConverter instance,
    significantly reducing processing time on subsequent runs from 15-20 minutes
    to just seconds.
    """
    # Signal handling for graceful shutdown
    shutdown_requested = False

    def signal_handler(signum: int, frame) -> None:  # noqa: ARG001
        """Handle shutdown signals gracefully."""
        nonlocal shutdown_requested
        signal_names: dict[int, str] = {signal.SIGTERM: "SIGTERM", signal.SIGINT: "SIGINT"}
        signal_name = signal_names.get(signum, f"signal {signum}")

        logger.debug(f"Docling worker received {signal_name}, initiating graceful shutdown...")
        shutdown_requested = True

        # Send shutdown notification to parent thread
        with suppress(Exception):
            queue.put({"error": f"Worker interrupted by {signal_name}", "shutdown": True})

        # NOTE: Do NOT call sys.exit() here. This function runs in a thread
        # (not a subprocess), so sys.exit() would raise SystemExit which can
        # crash the host process in single-worker setups. Instead, just set
        # the flag and let check_shutdown() terminate the worker loop.

    def check_shutdown() -> None:
        """Check if shutdown was requested and raise to unwind if so."""
        if shutdown_requested:
            logger.info("Shutdown requested, exiting worker...")

            with suppress(Exception):
                queue.put({"error": "Worker shutdown requested", "shutdown": True})

            raise _ShutdownRequestedError

    # Register signal handlers early
    try:
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
        logger.debug("Signal handlers registered for graceful shutdown")
    except (OSError, ValueError) as e:
        # Some signals might not be available on all platforms
        logger.warning(f"Warning: Could not register signal handlers: {e}")

    # Check for shutdown before heavy imports
    check_shutdown()

    try:
        from docling.datamodel.base_models import ConversionStatus, InputFormat  # noqa: F401
        from docling.datamodel.pipeline_options import OcrOptions, PdfPipelineOptions, VlmPipelineOptions  # noqa: F401
        from docling.document_converter import DocumentConverter, FormatOption, PdfFormatOption  # noqa: F401
        from docling.models.factories import get_ocr_factory  # noqa: F401
        from docling.pipeline.vlm_pipeline import VlmPipeline  # noqa: F401
        from langchain_docling.picture_description import PictureDescriptionLangChainOptions  # noqa: F401

        # Check for shutdown after imports
        check_shutdown()
        logger.debug("Docling dependencies loaded successfully")

    except ModuleNotFoundError:
        msg = (
            "Docling is an optional dependency of Langflow. "
            "Install with `uv pip install 'langflow[docling]'` "
            "or refer to the documentation"
        )
        queue.put({"error": msg})
        return
    except ImportError as e:
        # A different import failed (e.g., a transitive dependency); preserve details.
        queue.put({"error": f"Failed to import a Docling dependency: {e}"})
        return
    except KeyboardInterrupt:
        logger.warning("KeyboardInterrupt during imports, exiting...")
        queue.put({"error": "Worker interrupted during imports", "shutdown": True})
        return

    # Use cached converter instead of creating new one each time
    # This is the key optimization that eliminates 15-20 minute model load times
    def _get_converter() -> DocumentConverter:
        check_shutdown()  # Check before heavy operations

        # For now, we don't support pic_desc_config caching due to serialization complexity
        # This is a known limitation that can be addressed in a future enhancement
        if pic_desc_config:
            logger.warning(
                "Picture description with LLM is not yet supported with cached converters. "
                "Using non-cached converter for this request."
            )
            # Fall back to creating a new converter (old behavior)
            from docling.datamodel.base_models import InputFormat
            from docling.datamodel.pipeline_options import PdfPipelineOptions
            from docling.document_converter import DocumentConverter, FormatOption, PdfFormatOption
            from docling.models.factories import get_ocr_factory
            from langchain_docling.picture_description import PictureDescriptionLangChainOptions

            pipeline_options = PdfPipelineOptions()
            pipeline_options.do_ocr = ocr_engine not in {"", "None"}
            if pipeline_options.do_ocr:
                ocr_factory = get_ocr_factory(allow_external_plugins=False)
                ocr_options = ocr_factory.create_options(kind=ocr_engine)
                pipeline_options.ocr_options = ocr_options

            pipeline_options.do_picture_classification = do_picture_classification
            pic_desc_llm = _deserialize_pydantic_model(pic_desc_config)
            logger.info("Docling enabling the picture description stage.")
            pipeline_options.do_picture_description = True
            pipeline_options.allow_external_plugins = True
            pipeline_options.picture_description_options = PictureDescriptionLangChainOptions(
                llm=pic_desc_llm,
                prompt=pic_desc_prompt,
            )

            pdf_format_option = PdfFormatOption(pipeline_options=pipeline_options)
            format_options: dict[InputFormat, FormatOption] = {
                InputFormat.PDF: pdf_format_option,
                InputFormat.IMAGE: pdf_format_option,
            }
            return DocumentConverter(format_options=format_options)

        # Use cached converter - this is where the magic happens!
        # First run: creates and caches converter (15-20 min)
        # Subsequent runs: reuses cached converter (seconds)
        pic_desc_config_hash = None  # Will be None since we checked above
        return _get_cached_converter(
            pipeline=pipeline,
            ocr_engine=ocr_engine,
            do_picture_classification=do_picture_classification,
            pic_desc_config_hash=pic_desc_config_hash,
        )

    try:
        # Check for shutdown before creating converter (can be slow)
        check_shutdown()
        logger.info(f"Initializing {pipeline} pipeline with OCR: {ocr_engine or 'disabled'}")

        converter = _get_converter()

        # Check for shutdown before processing files
        check_shutdown()
        logger.info(f"Starting to process {len(file_paths)} files...")

        # Process files with periodic shutdown checks
        results = []
        for i, file_path in enumerate(file_paths):
            # Check for shutdown before processing each file
            check_shutdown()

            logger.debug(f"Processing file {i + 1}/{len(file_paths)}: {file_path}")

            try:
                single_result = converter.convert_all([file_path])
                results.extend(single_result)
                check_shutdown()

            except ImportError as import_error:
                # Simply pass ImportError to main process for handling
                queue.put(
                    {"error": str(import_error), "error_type": "import_error", "original_exception": "ImportError"}
                )
                return

            except (OSError, ValueError, RuntimeError) as file_error:
                error_msg = str(file_error)

                # Check for specific dependency errors and identify the dependency name
                dependency_name = None
                if "ocrmac is not correctly installed" in error_msg:
                    dependency_name = "ocrmac"
                elif "easyocr" in error_msg and "not installed" in error_msg:
                    dependency_name = "easyocr"
                elif "tesserocr" in error_msg and "not installed" in error_msg:
                    dependency_name = "tesserocr"
                elif "rapidocr" in error_msg and "not installed" in error_msg:
                    dependency_name = "rapidocr"

                if dependency_name:
                    queue.put(
                        {
                            "error": error_msg,
                            "error_type": "dependency_error",
                            "dependency_name": dependency_name,
                            "original_exception": type(file_error).__name__,
                        }
                    )
                    return

                # If not a dependency error, log and continue with other files
                logger.error(f"Error processing file {file_path}: {file_error}")
                check_shutdown()

            except Exception as file_error:  # noqa: BLE001
                logger.error(f"Unexpected error processing file {file_path}: {file_error}")
                check_shutdown()

        # Final shutdown check before sending results
        check_shutdown()

        # Process the results while maintaining the original structure
        processed_data = [
            {"document": res.document, "file_path": str(res.input.file), "status": res.status.name}
            if res.status == ConversionStatus.SUCCESS
            else None
            for res in results
        ]

        logger.info(f"Successfully processed {len([d for d in processed_data if d])} files")
        queue.put(processed_data)

    except _ShutdownRequestedError:
        logger.info("Docling worker stopped by shutdown request")
        return
    except KeyboardInterrupt:
        logger.warning("KeyboardInterrupt during processing, exiting gracefully...")
        queue.put({"error": "Worker interrupted during processing", "shutdown": True})
        return
    except Exception as e:  # noqa: BLE001
        if shutdown_requested:
            logger.exception("Exception occurred during shutdown, exiting...")
            return

        # Send any processing error to the main process with traceback
        error_info = {"error": str(e), "traceback": traceback.format_exc()}
        logger.error(f"Error in worker: {error_info}")
        queue.put(error_info)
    finally:
        logger.info("Docling worker finishing...")
        # Ensure we don't leave any hanging processes
        if shutdown_requested:
            logger.debug("Worker shutdown completed")
        else:
            logger.debug("Worker completed normally")