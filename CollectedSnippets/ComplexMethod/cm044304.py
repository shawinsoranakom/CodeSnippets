def format_type(type_: str, char_limit: int | None = None) -> str:
            """Format type in docstrings."""
            type_str = str(type_)

            # Apply the standard formatting first
            type_str = (
                type_str.replace("<class '", "")
                .replace("'>", "")
                .replace("typing.", "")
                .replace("pydantic.types.", "")
                .replace("datetime.date", "date")
                .replace("datetime.datetime", "datetime")
                .replace("NoneType", "None")
            )

            # Convert Optional[X] to X | None
            optional_pattern = r"Optional\[(.+?)\]"
            optional_match = re.search(optional_pattern, type_str)
            if optional_match:
                inner = optional_match.group(1)
                type_str = type_str.replace(f"Optional[{inner}]", f"{inner} | None")

            # Convert Union[X, Y, ...] to X | Y | ... format
            union_pattern = r"Union\[(.+)\]"
            union_match = re.search(union_pattern, type_str)
            if union_match:
                inner = union_match.group(1)
                # Split by comma, but be careful with nested types like list[str]
                parts = []
                depth = 0
                current = ""
                for char in inner:
                    if char == "[":
                        depth += 1
                    elif char == "]":
                        depth -= 1
                    elif char == "," and depth == 0:
                        parts.append(current.strip())
                        current = ""
                        continue
                    current += char
                if current.strip():
                    parts.append(current.strip())
                # Remove None and NoneType from parts, we'll add | None at the end if needed
                has_none = any(p in ("None", "NoneType") for p in parts)
                parts = [p for p in parts if p not in ("None", "NoneType")]
                type_str = " | ".join(parts)
                if has_none:
                    type_str += " | None"

            # Simplify Literal[...] to str (choices shown in description)
            # Handle Literal[...] | None -> str | None
            if "Literal[" in type_str:
                # Check if there's | None at the end
                has_none = type_str.endswith(" | None")
                # Replace any Literal[...] with str
                type_str = re.sub(r"Literal\[[^\]]+\]", "str", type_str)
                # Ensure | None is preserved
                if has_none and not type_str.endswith(" | None"):
                    type_str += " | None"

            # Clean up ", None" that might be left over
            type_str = type_str.replace(", None", "")

            # Deduplicate types while preserving order (e.g. str | str | str -> str)
            if " | " in type_str:
                parts = [p.strip() for p in type_str.split(" | ")]
                has_none = "None" in parts
                # Remove None for now, deduplicate, then add back
                parts = [p for p in parts if p != "None"]
                # Deduplicate while preserving order
                seen: set[str] = set()
                unique_parts = []
                for p in parts:
                    if p not in seen:
                        seen.add(p)
                        unique_parts.append(p)
                type_str = " | ".join(unique_parts)
                if has_none:
                    type_str += " | None"

            # Apply char_limit if specified (simple truncation with bracket balancing)
            if char_limit and len(type_str) > char_limit:
                truncated = type_str[:char_limit]
                open_brackets = truncated.count("[") - truncated.count("]")
                if open_brackets > 0:
                    truncated += "]" * open_brackets
                type_str = truncated

            return type_str