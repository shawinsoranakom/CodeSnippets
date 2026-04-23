def update_build_config(self, build_config, field_value, field_name=None):
        """Update build configuration to show/hide fields based on storage location selection."""
        # Update options dynamically based on cloud environment
        # This ensures options are refreshed when build_config is updated
        if "storage_location" in build_config:
            updated_options = _get_storage_location_options()
            build_config["storage_location"]["options"] = updated_options

        if field_name != "storage_location":
            return build_config

        # Extract selected storage location
        selected = [location["name"] for location in field_value] if isinstance(field_value, list) else []

        # Hide all dynamic fields first
        dynamic_fields = [
            "file_name",  # Common fields (input is always visible)
            "append_mode",
            "local_format",
            "aws_format",
            "gdrive_format",
            "aws_access_key_id",
            "aws_secret_access_key",
            "bucket_name",
            "aws_region",
            "s3_prefix",
            "service_account_key",
            "folder_id",
        ]

        for f_name in dynamic_fields:
            if f_name in build_config:
                build_config[f_name]["show"] = False

        # Show fields based on selected storage location
        if len(selected) == 1:
            location = selected[0]

            # Show file_name when any storage location is selected
            if "file_name" in build_config:
                build_config["file_name"]["show"] = True

            # Show append_mode only for Local storage (not supported for cloud storage)
            if "append_mode" in build_config:
                build_config["append_mode"]["show"] = location == "Local"

            if location == "Local":
                if "local_format" in build_config:
                    build_config["local_format"]["show"] = True

            elif location == "AWS":
                aws_fields = [
                    "aws_format",
                    "aws_access_key_id",
                    "aws_secret_access_key",
                    "bucket_name",
                    "aws_region",
                    "s3_prefix",
                ]
                for f_name in aws_fields:
                    if f_name in build_config:
                        build_config[f_name]["show"] = True
                        build_config[f_name]["advanced"] = False

            elif location == "Google Drive":
                gdrive_fields = ["gdrive_format", "service_account_key", "folder_id"]
                for f_name in gdrive_fields:
                    if f_name in build_config:
                        build_config[f_name]["show"] = True
                        build_config[f_name]["advanced"] = False

        return build_config