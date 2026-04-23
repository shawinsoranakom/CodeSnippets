def selector_func(element, context_sensitive=True):
                cache_key = None

                # Use result caching if enabled
                if self.use_caching:
                    # Create a cache key based on element and selector
                    element_id = element.get('id', '') or str(hash(element))
                    cache_key = f"{element_id}::{selector_str}"

                    if cache_key in self._result_cache:
                        return self._result_cache[cache_key]

                results = []
                try:
                    # Strategy 1: Direct CSS selector application (fastest)
                    results = compiled(element)

                    # If that fails and we need context sensitivity
                    if not results and context_sensitive:
                        # Strategy 2: Try XPath with context adjustment
                        context_xpath = self._make_context_sensitive_xpath(xpath, element)
                        if context_xpath:
                            results = element.xpath(context_xpath)

                        # Strategy 3: Handle special case - nth-child
                        if not results and 'nth-child' in original_selector:
                            results = self._handle_nth_child_selector(element, original_selector)

                        # Strategy 4: Direct descendant search for class/ID selectors
                        if not results:
                            results = self._fallback_class_id_search(element, original_selector)

                        # Strategy 5: Last resort - tag name search for the final part
                        if not results:
                            parts = original_selector.split()
                            if parts:
                                last_part = parts[-1]
                                # Extract tag name from the selector
                                tag_match = re.match(r'^(\w+)', last_part)
                                if tag_match:
                                    tag_name = tag_match.group(1)
                                    results = element.xpath(f".//{tag_name}")

                    # Cache results if caching is enabled
                    if self.use_caching and cache_key:
                        self._result_cache[cache_key] = results

                except Exception as e:
                    if self.verbose:
                        print(f"Error applying selector '{selector_str}': {e}")

                return results