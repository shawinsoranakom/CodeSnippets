def select_func(element):
                    try:
                        # First attempt: direct CSS selector application
                        results = compiled(element)
                        if results:
                            return results

                        # Second attempt: contextual XPath selection
                        # Convert the root-based XPath to a context-based XPath
                        xpath = compiled.path

                        # If the XPath already starts with descendant-or-self, handle it specially
                        if xpath.startswith('descendant-or-self::'):
                            context_xpath = xpath
                        else:
                            # For normal XPath expressions, make them relative to current context
                            context_xpath = f"./{xpath.lstrip('/')}"

                        results = element.xpath(context_xpath)
                        if results:
                            return results

                        # Final fallback: simple descendant search for common patterns
                        if 'nth-child' in selector_str:
                            # Handle td:nth-child(N) pattern
                            import re
                            match = re.search(r'td:nth-child\((\d+)\)', selector_str)
                            if match:
                                col_num = match.group(1)
                                sub_selector = selector_str.split(')', 1)[-1].strip()
                                if sub_selector:
                                    return element.xpath(f".//td[{col_num}]//{sub_selector}")
                                else:
                                    return element.xpath(f".//td[{col_num}]")

                        # Last resort: try each part of the selector separately
                        parts = selector_str.split()
                        if len(parts) > 1 and parts[-1]:
                            return element.xpath(f".//{parts[-1]}")

                        return []
                    except Exception as e:
                        if self.verbose:
                            print(f"Error applying selector '{selector_str}': {e}")
                        return []