def get_array_size(array_str: str) -> int:
                # Remove braces and whitespace
                content = array_str.strip()
                if content.startswith("{") and content.endswith("}"):
                    content = content[1:-1].strip()

                if not content:  # Empty array
                    return 0

                # Count elements by counting commas, accounting for nested structures
                depth = 0
                comma_count = 0
                for char in content:
                    if char in "({[<":
                        depth += 1
                    elif char in ")}]>":
                        depth -= 1
                    elif char == "," and depth == 0:
                        comma_count += 1

                return comma_count + 1