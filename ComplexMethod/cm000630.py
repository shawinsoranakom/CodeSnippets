def search_in_content(elements: list[dict]) -> None:
            """Recursively search through content elements."""
            for element in elements:
                if "paragraph" in element:
                    for text_elem in element["paragraph"].get("elements", []):
                        if "textRun" in text_elem:
                            text_run = text_elem["textRun"]
                            text_content = text_run.get("content", "")
                            start_index = text_elem.get("startIndex", 0)

                            # Search within this text run
                            text_to_search = (
                                text_content if match_case else text_content.lower()
                            )
                            offset = 0
                            while True:
                                pos = text_to_search.find(search_text, offset)
                                if pos == -1:
                                    break
                                # Calculate actual document indices
                                doc_start = start_index + pos
                                doc_end = doc_start + len(find_text)
                                positions.append((doc_start, doc_end))
                                offset = pos + 1

                elif "table" in element:
                    # Search within table cells
                    for row in element["table"].get("tableRows", []):
                        for cell in row.get("tableCells", []):
                            search_in_content(cell.get("content", []))