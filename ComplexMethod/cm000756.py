async def run(
        self, input_data: Input, *, credentials: APIKeyCredentials, **kwargs
    ) -> BlockOutput:
        # Use AsyncExa SDK
        aexa = self._get_client(credentials.api_key.get_secret_value())

        try:
            all_items = []

            # Use SDK's list_all iterator to fetch items
            item_iterator = aexa.websets.items.list_all(
                webset_id=input_data.webset_id, limit=input_data.max_items
            )

            async for sdk_item in item_iterator:
                if len(all_items) >= input_data.max_items:
                    break

                # Convert to dict for export
                item_dict = sdk_item.model_dump(by_alias=True, exclude_none=True)
                all_items.append(item_dict)

            # Calculate total and truncated
            total_items = len(all_items)  # SDK doesn't provide total count
            truncated = len(all_items) >= input_data.max_items

            # Process items based on include flags
            if not input_data.include_content:
                for item in all_items:
                    item.pop("content", None)

            if not input_data.include_enrichments:
                for item in all_items:
                    item.pop("enrichments", None)

            # Format the export data
            export_data = ""

            if input_data.format == ExportFormat.JSON:
                export_data = json.dumps(all_items, indent=2, default=str)

            elif input_data.format == ExportFormat.JSON_LINES:
                lines = [json.dumps(item, default=str) for item in all_items]
                export_data = "\n".join(lines)

            elif input_data.format == ExportFormat.CSV:
                # Extract all unique keys for CSV headers
                all_keys = set()
                for item in all_items:
                    all_keys.update(self._flatten_dict(item).keys())

                # Create CSV
                output = StringIO()
                writer = csv.DictWriter(output, fieldnames=sorted(all_keys))
                writer.writeheader()

                for item in all_items:
                    flat_item = self._flatten_dict(item)
                    writer.writerow(flat_item)

                export_data = output.getvalue()

            yield "export_data", export_data
            yield "item_count", len(all_items)
            yield "total_items", total_items
            yield "truncated", truncated
            yield "format", input_data.format.value

        except ValueError as e:
            # Re-raise user input validation errors
            raise ValueError(f"Failed to export webset: {e}") from e