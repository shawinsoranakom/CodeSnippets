def update_build_config(self, build_config: dict, field_value: str, field_name: str | None = None) -> dict:
        """Update the build configuration when the mode changes."""
        if field_name == "mode":
            # Hide all dynamic fields by default
            dynamic_fields = [
                "ingest_data",
                "search_query",
                "search_type",
                "number_of_results",
                "existing_collections",
                "collection_name",
                "embedding",
                "allow_duplicates",
                "limit",
            ]
            for field in dynamic_fields:
                if field in build_config:
                    build_config[field]["show"] = False

            # Show/hide fields based on selected mode
            if field_value == "Ingest":
                if "ingest_data" in build_config:
                    build_config["ingest_data"]["show"] = True
                if "collection_name" in build_config:
                    build_config["collection_name"]["show"] = True
                    build_config["collection_name"]["display_name"] = "Name Your Collection"
                if "persist" in build_config:
                    build_config["persist"]["show"] = True
                if "persist_directory" in build_config:
                    build_config["persist_directory"]["show"] = True
                if "embedding" in build_config:
                    build_config["embedding"]["show"] = True
                if "allow_duplicates" in build_config:
                    build_config["allow_duplicates"]["show"] = True
                if "limit" in build_config:
                    build_config["limit"]["show"] = True
            elif field_value == "Retrieve":
                if "persist" in build_config:
                    build_config["persist"]["show"] = False
                build_config["search_query"]["show"] = True
                build_config["search_type"]["show"] = True
                build_config["number_of_results"]["show"] = True
                build_config["embedding"]["show"] = True
                build_config["collection_name"]["show"] = False
                # Show existing collections dropdown and update its options
                if "existing_collections" in build_config:
                    build_config["existing_collections"]["show"] = True
                    build_config["existing_collections"]["options"] = self.list_existing_collections()
                # Hide collection_name in Retrieve mode since we use existing_collections
        elif field_name == "existing_collections":
            # Update collection_name when an existing collection is selected
            if "collection_name" in build_config:
                build_config["collection_name"]["value"] = field_value

        return build_config