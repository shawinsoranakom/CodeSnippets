def add_context(available_paths: set[str], context_name: str, context_filter: c.Callable[[str], bool]) -> None:
            """Add the specified context to the context list, consuming available paths that match the given context filter."""
            filtered_paths = set(p for p in available_paths if context_filter(p))

            if selected_paths := sorted(path for path in filtered_paths if path in target_paths):
                contexts.append((context_name, True, selected_paths))

            if selected_paths := sorted(path for path in filtered_paths if path not in target_paths):
                contexts.append((context_name, False, selected_paths))

            available_paths -= filtered_paths