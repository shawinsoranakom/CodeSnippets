def parse_pdf(
        self,
        filepath: str | PathLike[str],
        binary: BytesIO | bytes | None = None,
        callback: Optional[Callable[[float, str], None]] = None,
        *,
        parse_method: str = "raw",
        api_url: Optional[str] = None,
        access_token: Optional[str] = None,
        algorithm: Optional[AlgorithmType] = None,
        request_timeout: Optional[int] = None,
        prettify_markdown: Optional[bool] = None,
        show_formula_number: Optional[bool] = None,
        visualize: Optional[bool] = None,
        additional_params: Optional[dict[str, Any]] = None,
        algorithm_config: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ) -> ParseResult:
        """Parse PDF document using PaddleOCR API."""
        self.outlines = extract_pdf_outlines(binary if binary is not None else filepath)
        # Create configuration - pass all kwargs to capture VL config parameters
        config_dict = {
            "api_url": api_url if api_url is not None else self.api_url,
            "access_token": access_token if access_token is not None else self.access_token,
            "algorithm": algorithm if algorithm is not None else self.algorithm,
            "request_timeout": request_timeout if request_timeout is not None else self.request_timeout,
        }
        if prettify_markdown is not None:
            config_dict["prettify_markdown"] = prettify_markdown
        if show_formula_number is not None:
            config_dict["show_formula_number"] = show_formula_number
        if visualize is not None:
            config_dict["visualize"] = visualize
        if additional_params is not None:
            config_dict["additional_params"] = additional_params
        if algorithm_config is not None:
            config_dict["algorithm_config"] = algorithm_config

        cfg = PaddleOCRConfig.from_dict(config_dict)

        if not cfg.api_url:
            raise RuntimeError("[PaddleOCR] API URL missing")

        # Prepare file data and generate page images for cropping
        data_bytes = self._prepare_file_data(filepath, binary)

        # Generate page images for cropping functionality
        input_source = filepath if binary is None else binary
        try:
            self.__images__(input_source, callback=callback)
        except Exception as e:
            self.logger.warning(f"[PaddleOCR] Failed to generate page images for cropping: {e}")

        # Build and send request
        result = self._send_request(data_bytes, cfg, callback)

        # Process response
        sections = self._transfer_to_sections(result, algorithm=cfg.algorithm, parse_method=parse_method)
        if callback:
            callback(0.9, f"[PaddleOCR] done, sections: {len(sections)}")

        tables = self._transfer_to_tables(result)
        if callback:
            callback(1.0, f"[PaddleOCR] done, tables: {len(tables)}")

        return sections, tables