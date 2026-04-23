def _process_element(
            element: ResultSet[Tag],
            documents: list[Document],
            current_headers: dict[str, str],
            current_content: list[str],
            preserved_elements: dict[str, str],
            placeholder_count: int,
        ) -> tuple[list[Document], dict[str, str], list[str], dict[str, str], int]:
            for elem in element:
                if elem.name in [h[0] for h in self._headers_to_split_on]:
                    if current_content:
                        documents.extend(
                            self._create_documents(
                                current_headers,
                                " ".join(current_content),
                                preserved_elements,
                            )
                        )
                        current_content.clear()
                        preserved_elements.clear()
                    header_name = elem.get_text(strip=True)
                    current_headers = {
                        dict(self._headers_to_split_on)[elem.name]: header_name
                    }
                elif elem.name in self._elements_to_preserve:
                    placeholder = f"PRESERVED_{placeholder_count}"
                    preserved_elements[placeholder] = _get_element_text(elem)
                    current_content.append(placeholder)
                    placeholder_count += 1
                else:
                    # Recursively process children to find nested headers or
                    # preserved elements.
                    children = _find_all_tags(elem, recursive=False)
                    if children:
                        # Element has children - recursively process them.
                        (
                            documents,
                            current_headers,
                            current_content,
                            preserved_elements,
                            placeholder_count,
                        ) = _process_element(
                            children,
                            documents,
                            current_headers,
                            current_content,
                            preserved_elements,
                            placeholder_count,
                        )
                        # After processing children, extract only text
                        # strings from this element (not its children). Used
                        # recursive=False to avoid double-counting.
                        content = " ".join(_find_all_strings(elem, recursive=False))
                        if content:
                            content = self._normalize_and_clean_text(content)
                            current_content.append(content)
                    else:
                        # Leaf element with no children, so we extract its
                        # text and add to current content. Handles
                        # text-only elements like <p>, <span>, <div>
                        content = _get_element_text(elem)
                        if content:
                            current_content.append(content)

            return (
                documents,
                current_headers,
                current_content,
                preserved_elements,
                placeholder_count,
            )