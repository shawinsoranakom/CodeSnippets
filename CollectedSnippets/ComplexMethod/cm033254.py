def _split_combined_values(cls, meta_fields: Dict) -> Dict:
        """
        Post-process metadata to split combined values by common delimiters.

        For example: "关羽、孙权、张辽" -> ["关羽", "孙权", "张辽"]
        This fixes LLM extraction where multiple values are extracted as one combined value.
        Also removes duplicates after splitting.

        Args:
            meta_fields: Metadata dictionary

        Returns:
            Processed metadata with split values
        """
        if not meta_fields or not isinstance(meta_fields, dict):
            return meta_fields

        processed = {}
        for key, value in meta_fields.items():
            if isinstance(value, list):
                # Process each item in the list
                new_values = []
                for item in value:
                    if isinstance(item, str):
                        # Split by common delimiters: Chinese comma (、), regular comma (,), pipe (|), semicolon (;), Chinese semicolon (；)
                        # Also handle mixed delimiters and spaces
                        split_items = re.split(r'[、,，;；|]+', item.strip())
                        # Trim whitespace and filter empty strings
                        split_items = [s.strip() for s in split_items if s.strip()]
                        if split_items:
                            new_values.extend(split_items)
                        else:
                            # Keep original if no split happened
                            new_values.append(item)
                    else:
                        new_values.append(item)
                # Remove duplicates while preserving order.
                # Use string-based dedupe to support unhashable values (e.g. dict entries).
                processed[key] = dedupe_list(new_values)
            else:
                processed[key] = value

        if processed != meta_fields:
            logging.debug(f"[METADATA SPLIT] Split combined values: {meta_fields} -> {processed}")
        return processed