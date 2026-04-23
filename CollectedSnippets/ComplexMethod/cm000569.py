async def run(self, input_data: Input, **kwargs) -> BlockOutput:
        # Security fix: Add limits to prevent DoS from large iterations
        MAX_ITEMS = 10000  # Maximum items to iterate
        MAX_ITEM_SIZE = 1024 * 1024  # 1MB per item

        for data in [input_data.items, input_data.items_object, input_data.items_str]:
            if not data:
                continue

            # Limit string size before parsing
            if isinstance(data, str):
                if len(data) > MAX_ITEM_SIZE:
                    raise ValueError(
                        f"Input too large: {len(data)} bytes > {MAX_ITEM_SIZE} bytes"
                    )
                items = loads(data)
            else:
                items = data

            # Check total item count
            if isinstance(items, (list, dict)):
                if len(items) > MAX_ITEMS:
                    raise ValueError(f"Too many items: {len(items)} > {MAX_ITEMS}")

            iteration_count = 0
            if isinstance(items, dict):
                # If items is a dictionary, iterate over its values
                for key, value in items.items():
                    if iteration_count >= MAX_ITEMS:
                        break
                    yield "item", value
                    yield "key", key  # Fixed: should yield key, not item
                    iteration_count += 1
            else:
                # If items is a list, iterate over the list
                for index, item in enumerate(items):
                    if iteration_count >= MAX_ITEMS:
                        break
                    yield "item", item
                    yield "key", index
                    iteration_count += 1