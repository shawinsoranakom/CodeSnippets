def _populate_actions_data(self):
        """Fetch the list of actions for the toolkit and build helper maps."""
        if self._actions_data:
            return

        # Try to load from the class-level cache
        toolkit_slug = self.app_name.lower()
        if toolkit_slug in self.__class__.get_actions_cache():
            # Deep-copy so that any mutation on this instance does not affect the
            # cached master copy.
            self._actions_data = copy.deepcopy(self.__class__.get_actions_cache()[toolkit_slug])
            self._action_schemas = copy.deepcopy(self.__class__.get_action_schema_cache().get(toolkit_slug, {}))
            logger.debug(f"Loaded actions for {toolkit_slug} from in-process cache")
            return

        api_key = getattr(self, "api_key", None)
        if not api_key:
            logger.warning("API key is missing. Cannot populate actions data.")
            return

        try:
            composio = self._build_wrapper()
            toolkit_slug = self.app_name.lower()

            raw_tools = composio.tools.get_raw_composio_tools(toolkits=[toolkit_slug], limit=999)

            if not raw_tools:
                msg = f"Toolkit '{toolkit_slug}' not found or has no available tools"
                raise ValueError(msg)

            for raw_tool in raw_tools:
                try:
                    # Convert raw_tool to dict-like structure
                    tool_dict = raw_tool.__dict__ if hasattr(raw_tool, "__dict__") else raw_tool

                    if not tool_dict:
                        logger.warning(f"Tool is None or empty: {raw_tool}")
                        continue

                    action_key = tool_dict.get("slug")
                    if not action_key:
                        logger.warning(f"Action key (slug) is missing in tool: {tool_dict}")
                        continue

                    # Human-friendly display name
                    display_name = tool_dict.get("name") or tool_dict.get("display_name")
                    if not display_name:
                        # Better fallback: convert GMAIL_SEND_EMAIL to "Send Email"
                        # Remove app prefix and convert to title case
                        clean_name = action_key
                        clean_name = clean_name.removeprefix(f"{self.app_name.upper()}_")
                        # Convert underscores to spaces and title case
                        display_name = clean_name.replace("_", " ").title()

                    # Build list of parameter names and track bool fields
                    parameters_schema = tool_dict.get("input_parameters", {})
                    if parameters_schema is None:
                        logger.warning(f"Parameters schema is None for action key: {action_key}")
                        # Still add the action but with empty fields
                        # Extract version information from the tool
                        version = tool_dict.get("version")
                        available_versions = tool_dict.get("available_versions", [])

                        self._action_schemas[action_key] = tool_dict
                        self._actions_data[action_key] = {
                            "display_name": display_name,
                            "action_fields": [],
                            "file_upload_fields": set(),
                            "version": version,
                            "available_versions": available_versions,
                        }
                        continue

                    try:
                        # Special handling for unusual schema structures
                        if not isinstance(parameters_schema, dict):
                            # Try to convert if it's a model object
                            if hasattr(parameters_schema, "model_dump"):
                                parameters_schema = parameters_schema.model_dump()
                            elif hasattr(parameters_schema, "__dict__"):
                                parameters_schema = parameters_schema.__dict__
                            else:
                                logger.warning(f"Cannot process parameters schema for {action_key}, skipping")
                                # Extract version information from the tool
                                version = tool_dict.get("version")
                                available_versions = tool_dict.get("available_versions", [])

                                self._action_schemas[action_key] = tool_dict
                                self._actions_data[action_key] = {
                                    "display_name": display_name,
                                    "action_fields": [],
                                    "file_upload_fields": set(),
                                    "version": version,
                                    "available_versions": available_versions,
                                }
                                continue

                        # Validate parameters_schema has required structure before flattening
                        if not parameters_schema.get("properties") and not parameters_schema.get("$defs"):
                            # Create a minimal valid schema to avoid errors
                            parameters_schema = {"type": "object", "properties": {}}

                        # Sanitize the schema before passing to flatten_schema
                        # Handle case where 'required' is explicitly None (causes "'NoneType' object is not iterable")
                        if parameters_schema.get("required") is None:
                            parameters_schema = parameters_schema.copy()  # Don't modify the original
                            parameters_schema["required"] = []

                        try:
                            # Preserve original descriptions before flattening to restore if lost
                            original_descriptions = {}
                            original_props = parameters_schema.get("properties", {})
                            for prop_name, prop_schema in original_props.items():
                                if isinstance(prop_schema, dict) and "description" in prop_schema:
                                    original_descriptions[prop_name] = prop_schema["description"]

                            flat_schema = flatten_schema(parameters_schema)

                            # Restore lost descriptions in flattened schema
                            if flat_schema and isinstance(flat_schema, dict) and "properties" in flat_schema:
                                flat_props = flat_schema["properties"]
                                for field_name, field_schema in flat_props.items():
                                    # Check if this field lost its description during flattening
                                    if isinstance(field_schema, dict) and "description" not in field_schema:
                                        # Try to find the original description
                                        # Handle array fields like bcc[0] -> bcc
                                        base_field_name = field_name.replace("[0]", "")
                                        if base_field_name in original_descriptions:
                                            field_schema["description"] = original_descriptions[base_field_name]
                                        elif field_name in original_descriptions:
                                            field_schema["description"] = original_descriptions[field_name]
                        except (KeyError, TypeError, ValueError):
                            # Extract version information from the tool
                            version = tool_dict.get("version")
                            available_versions = tool_dict.get("available_versions", [])

                            self._action_schemas[action_key] = tool_dict
                            self._actions_data[action_key] = {
                                "display_name": display_name,
                                "action_fields": [],
                                "file_upload_fields": set(),
                                "version": version,
                                "available_versions": available_versions,
                            }
                            continue

                        if flat_schema is None:
                            logger.warning(f"Flat schema is None for action key: {action_key}")
                            # Still add the action but with empty fields so the UI doesn't break
                            # Extract version information from the tool
                            version = tool_dict.get("version")
                            available_versions = tool_dict.get("available_versions", [])

                            self._action_schemas[action_key] = tool_dict
                            self._actions_data[action_key] = {
                                "display_name": display_name,
                                "action_fields": [],
                                "file_upload_fields": set(),
                                "version": version,
                                "available_versions": available_versions,
                            }
                            continue

                        # Extract field names and detect file upload fields during parsing
                        raw_action_fields = list(flat_schema.get("properties", {}).keys())
                        action_fields = []
                        attachment_related_found = False
                        file_upload_fields = set()

                        # Check original schema properties for file_uploadable fields
                        original_props = parameters_schema.get("properties", {})

                        # Determine top-level fields that should be treated as single JSON inputs
                        json_parent_fields = set()
                        for top_name, top_schema in original_props.items():
                            if isinstance(top_schema, dict) and top_schema.get("type") in {"object", "array"}:
                                json_parent_fields.add(top_name)

                        for field_name, field_schema in original_props.items():
                            if isinstance(field_schema, dict):
                                clean_field_name = field_name.replace("[0]", "")
                                # Check direct file_uploadable attribute
                                if field_schema.get("file_uploadable") is True:
                                    file_upload_fields.add(clean_field_name)

                                # Check anyOf structures (like OUTLOOK_OUTLOOK_SEND_EMAIL)
                                if "anyOf" in field_schema:
                                    for any_of_item in field_schema["anyOf"]:
                                        if isinstance(any_of_item, dict) and any_of_item.get("file_uploadable") is True:
                                            file_upload_fields.add(clean_field_name)

                        for field in raw_action_fields:
                            clean_field = field.replace("[0]", "")
                            # Skip subfields of JSON parents; we will expose the parent as a single field
                            top_prefix = clean_field.split(".")[0].split("[")[0]
                            if top_prefix in json_parent_fields and "." in clean_field:
                                continue
                            # Check if this field is attachment-related
                            if clean_field.lower().startswith("attachment."):
                                attachment_related_found = True
                                continue  # Skip individual attachment fields

                            # Handle reserved attribute name conflicts
                            # Prefix with app name to prevent clashes with component attributes
                            if clean_field in self.RESERVED_ATTRIBUTES:
                                clean_field = f"{self.app_name}_{clean_field}"

                            action_fields.append(clean_field)

                        # Add consolidated attachment field if we found attachment-related fields
                        if attachment_related_found:
                            action_fields.append("attachment")
                            file_upload_fields.add("attachment")  # Attachment fields are also file upload fields

                        # Ensure parents for object/array are present as fields (single JSON field)
                        for parent in json_parent_fields:
                            if parent not in action_fields:
                                action_fields.append(parent)

                        # Track boolean parameters so we can coerce them later
                        properties = flat_schema.get("properties", {})
                        if properties:
                            for p_name, p_schema in properties.items():
                                if isinstance(p_schema, dict) and p_schema.get("type") == "boolean":
                                    # Use cleaned field name for boolean tracking
                                    clean_field_name = p_name.replace("[0]", "")
                                    self._bool_variables.add(clean_field_name)

                        # Extract version information from the tool
                        version = tool_dict.get("version")
                        available_versions = tool_dict.get("available_versions", [])

                        self._action_schemas[action_key] = tool_dict
                        self._actions_data[action_key] = {
                            "display_name": display_name,
                            "action_fields": action_fields,
                            "file_upload_fields": file_upload_fields,
                            "version": version,
                            "available_versions": available_versions,
                        }

                    except (KeyError, TypeError, ValueError) as flatten_error:
                        logger.error(f"flatten_schema failed for {action_key}: {flatten_error}")
                        # Extract version information from the tool
                        version = tool_dict.get("version")
                        available_versions = tool_dict.get("available_versions", [])

                        self._action_schemas[action_key] = tool_dict
                        self._actions_data[action_key] = {
                            "display_name": display_name,
                            "action_fields": [],
                            "file_upload_fields": set(),
                            "version": version,
                            "available_versions": available_versions,
                        }
                        continue

                except ValueError as e:
                    logger.warning(f"Failed processing Composio tool for action {raw_tool}: {e}")

            # Helper look-ups used elsewhere
            self._all_fields = {f for d in self._actions_data.values() for f in d["action_fields"]}
            self._build_action_maps()

            # Cache actions for this toolkit so subsequent component instances
            # can reuse them without hitting the Composio API again.
            self.__class__.get_actions_cache()[toolkit_slug] = copy.deepcopy(self._actions_data)
            self.__class__.get_action_schema_cache()[toolkit_slug] = copy.deepcopy(self._action_schemas)

        except ValueError as e:
            logger.debug(f"Could not populate Composio actions for {self.app_name}: {e}")