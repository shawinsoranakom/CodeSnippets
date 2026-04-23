def update_build_config(
        self,
        build_config: dict[str, Any],
        field_value: Any,
        field_name: str | None = None,
    ) -> dict[str, Any]:
        """Show/hide Advanced Parser and related fields based on selection context."""
        # Update storage location options dynamically based on cloud environment
        if "storage_location" in build_config:
            updated_options = _get_storage_location_options()
            build_config["storage_location"]["options"] = updated_options

        # Handle storage location selection
        if field_name == "storage_location":
            # Extract selected storage location
            selected = [location["name"] for location in field_value] if isinstance(field_value, list) else []

            # Hide all storage-specific fields first
            storage_fields = [
                "aws_access_key_id",
                "aws_secret_access_key",
                "bucket_name",
                "aws_region",
                "s3_file_key",
                "service_account_key",
                "file_id",
            ]

            for f_name in storage_fields:
                if f_name in build_config:
                    build_config[f_name]["show"] = False

            # Show fields based on selected storage location
            if len(selected) == 1:
                location = selected[0]

                if location == "Local":
                    # Show file upload input for local storage
                    if "path" in build_config:
                        build_config["path"]["show"] = True

                elif location == "AWS":
                    # Hide file upload input, show AWS fields
                    if "path" in build_config:
                        build_config["path"]["show"] = False

                    aws_fields = [
                        "aws_access_key_id",
                        "aws_secret_access_key",
                        "bucket_name",
                        "aws_region",
                        "s3_file_key",
                    ]
                    for f_name in aws_fields:
                        if f_name in build_config:
                            build_config[f_name]["show"] = True
                            build_config[f_name]["advanced"] = False

                elif location == "Google Drive":
                    # Hide file upload input, show Google Drive fields
                    if "path" in build_config:
                        build_config["path"]["show"] = False

                    gdrive_fields = ["service_account_key", "file_id"]
                    for f_name in gdrive_fields:
                        if f_name in build_config:
                            build_config[f_name]["show"] = True
                            build_config[f_name]["advanced"] = False
            # No storage location selected - show file upload by default
            elif "path" in build_config:
                build_config["path"]["show"] = True

            return build_config

        if field_name == "path":
            paths = self._path_value(build_config)

            # Disable in cloud environments
            if is_astra_cloud_environment():
                self._disable_docling_fields_in_cloud(build_config)
            else:
                # If all files can be processed by docling, do so
                allow_advanced = all(not file_path.endswith((".csv", ".xlsx", ".parquet")) for file_path in paths)
                build_config["advanced_mode"]["show"] = allow_advanced
                if not allow_advanced:
                    build_config["advanced_mode"]["value"] = False
                    docling_fields = (
                        "pipeline",
                        "ocr_engine",
                        "doc_key",
                        "md_image_placeholder",
                        "md_page_break_placeholder",
                    )
                    for field in docling_fields:
                        if field in build_config:
                            build_config[field]["show"] = False

        # Docling Processing
        elif field_name == "advanced_mode":
            # Disable in cloud environments - don't show Docling fields even if advanced_mode is toggled
            if is_astra_cloud_environment():
                self._disable_docling_fields_in_cloud(build_config)
            else:
                docling_fields = (
                    "pipeline",
                    "ocr_engine",
                    "doc_key",
                    "md_image_placeholder",
                    "md_page_break_placeholder",
                )
                for field in docling_fields:
                    if field in build_config:
                        build_config[field]["show"] = bool(field_value)
                        if field == "pipeline":
                            build_config[field]["advanced"] = not bool(field_value)

        elif field_name == "pipeline":
            # Disable in cloud environments - don't show OCR engine even if pipeline is changed
            if is_astra_cloud_environment():
                self._disable_docling_fields_in_cloud(build_config)
            elif field_value == "standard":
                build_config["ocr_engine"]["show"] = True
                build_config["ocr_engine"]["value"] = "easyocr"
            else:
                build_config["ocr_engine"]["show"] = False
                build_config["ocr_engine"]["value"] = "None"

        return build_config