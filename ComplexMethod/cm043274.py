def _scrap(
        self,
        url: str,
        html: str,
        word_count_threshold: int = MIN_WORD_THRESHOLD,
        css_selector: str = None,
        target_elements: List[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        if not html:
            return None

        success = True
        try:
            doc = lhtml.document_fromstring(html)
            # Match BeautifulSoup's behavior of using body or full doc
            # body = doc.xpath('//body')[0] if doc.xpath('//body') else doc
            body = doc

            base_domain = get_base_domain(url)

            # Extract page context for link scoring (if enabled) - do this BEFORE any removals
            page_context = None
            if kwargs.get("score_links", False):
                try:
                    # Extract title
                    title_elements = doc.xpath('//title')
                    page_title = title_elements[0].text_content() if title_elements else ""

                    # Extract headlines
                    headlines = []
                    for tag in ['h1', 'h2', 'h3']:
                        elements = doc.xpath(f'//{tag}')
                        for el in elements:
                            text = el.text_content().strip()
                            if text:
                                headlines.append(text)
                    headlines_text = ' '.join(headlines)

                    # Extract meta description
                    meta_desc_elements = doc.xpath('//meta[@name="description"]/@content')
                    meta_description = meta_desc_elements[0] if meta_desc_elements else ""

                    # Create page context
                    page_context = extract_page_context(page_title, headlines_text, meta_description, url)
                except Exception:
                    page_context = {}  # Fail gracefully

            # Early removal of all images if exclude_all_images is set
            # This is more efficient in lxml as we remove elements before any processing
            if kwargs.get("exclude_all_images", False):
                for img in body.xpath('//img'):
                    if img.getparent() is not None:
                        img.getparent().remove(img)

            # Add comment removal
            if kwargs.get("remove_comments", False):
                comments = body.xpath("//comment()")
                for comment in comments:
                    comment.getparent().remove(comment)

            # Handle tag-based removal first
            excluded_tags = set(kwargs.get("excluded_tags", []) or [])
            if excluded_tags:
                for tag in excluded_tags:
                    for element in body.xpath(f".//{tag}"):
                        if element.getparent() is not None:
                            element.getparent().remove(element)

            # Handle CSS selector-based exclusion
            excluded_selector = kwargs.get("excluded_selector", "")
            if excluded_selector:
                try:
                    for element in body.cssselect(excluded_selector):
                        if element.getparent() is not None:
                            element.getparent().remove(element)
                except Exception as e:
                    self._log(
                        "error", f"Error with excluded CSS selector: {str(e)}", "SCRAPE"
                    )

            # Extract metadata before any content filtering
            try:
                meta = extract_metadata_using_lxml(
                    "", doc
                )  # Using same function as BeautifulSoup version
            except Exception as e:
                self._log("error", f"Error extracting metadata: {str(e)}", "SCRAPE")
                meta = {}

            content_element = None
            if css_selector:
                try:
                    selected = body.cssselect(css_selector)
                    if selected:
                        content_element = lhtml.Element("div")
                        content_element.extend(copy.deepcopy(selected))
                    else:
                        content_element = body
                except Exception as e:
                    self._log("error", f"Error with css_selector: {str(e)}", "SCRAPE")
                    content_element = body

            if target_elements:
                try:
                    source = content_element if content_element is not None else body
                    for_content_targeted_element = []
                    for target_element in target_elements:
                        for_content_targeted_element.extend(source.cssselect(target_element))
                    content_element = lhtml.Element("div")
                    content_element.extend(copy.deepcopy(for_content_targeted_element))
                except Exception as e:
                    self._log("error", f"Error with target element detection: {str(e)}", "SCRAPE")
                    return None
            elif content_element is None:
                content_element = body

            # Remove script and style tags
            for tag in ["style", "link", "meta", "noscript"]:
                for element in body.xpath(f".//{tag}"):
                    if element.getparent() is not None:
                        element.getparent().remove(element)

            # Handle script separately
            for element in body.xpath(f".//script"):
                parent = element.getparent()
                if parent is not None:
                    tail = element.tail  # Get the tail text
                    if tail:
                        prev = element.getprevious()  # Get the previous sibling node
                        if prev is not None:
                            if prev.tail:
                                prev.tail += tail 
                            else:
                                prev.tail = tail
                        else:
                            if parent.text:
                                parent.text += tail
                            else:
                                parent.text = tail
                    parent.remove(element)  # Delete the element


            # Handle social media and domain exclusions
            kwargs["exclude_domains"] = set(kwargs.get("exclude_domains", []))
            if kwargs.get("exclude_social_media_links", False):
                kwargs["exclude_social_media_domains"] = set(
                    kwargs.get("exclude_social_media_domains", [])
                    + SOCIAL_MEDIA_DOMAINS
                )
                kwargs["exclude_domains"].update(kwargs["exclude_social_media_domains"])

            # Process forms if needed
            if kwargs.get("remove_forms", False):
                for form in body.xpath(".//form"):
                    if form.getparent() is not None:
                        form.getparent().remove(form)

            # Process content
            media = {"images": [], "videos": [], "audios": [], "tables": []}
            internal_links_dict = {}
            external_links_dict = {}

            self._process_element(
                url,
                body,
                media,
                internal_links_dict,
                external_links_dict,
                page_context=page_context,
                base_domain=base_domain,
                **kwargs,
            )

            # Extract tables using the table extraction strategy if provided
            if 'table' not in excluded_tags:
                table_extraction = kwargs.get('table_extraction')
                if table_extraction:
                    # Pass logger to the strategy if it doesn't have one
                    if not table_extraction.logger:
                        table_extraction.logger = self.logger
                    # Extract tables using the strategy
                    extracted_tables = table_extraction.extract_tables(body, **kwargs)
                    media["tables"].extend(extracted_tables)

            # Handle only_text option
            if kwargs.get("only_text", False):
                for tag in ONLY_TEXT_ELIGIBLE_TAGS:
                    for element in body.xpath(f".//{tag}"):
                        if element.text:
                            new_text = lhtml.Element("span")
                            new_text.text = element.text_content()
                            if element.getparent() is not None:
                                element.getparent().replace(element, new_text)

            # Clean base64 images
            for img in body.xpath(".//img[@src]"):
                src = img.get("src", "")
                if self.BASE64_PATTERN.match(src):
                    img.set("src", self.BASE64_PATTERN.sub("", src))

            # Remove empty elements
            self.remove_empty_elements_fast(body, 1)

            # Remove unneeded attributes
            self.remove_unwanted_attributes_fast(
                body, keep_data_attributes=kwargs.get("keep_data_attributes", False)
            )

            # Generate output HTML
            cleaned_html = lhtml.tostring(
                # body,   
                content_element,
                encoding="unicode",
                pretty_print=True,
                method="html",
                with_tail=False,
            ).strip()

            # Create links dictionary in the format expected by LinkPreview
            links = {
                "internal": list(internal_links_dict.values()),
                "external": list(external_links_dict.values()),
            }

            # Extract head content for links if configured
            link_preview_config = kwargs.get("link_preview_config")
            if link_preview_config is not None:
                try:
                    import asyncio
                    from .link_preview import LinkPreview
                    from .models import Links, Link

                    verbose = link_preview_config.verbose

                    if verbose:
                        self._log("info", "Starting link head extraction for {internal} internal and {external} external links",
                                  params={"internal": len(links["internal"]), "external": len(links["external"])}, tag="LINK_EXTRACT")

                    # Convert dict links to Link objects
                    internal_links = [Link(**link_data) for link_data in links["internal"]]
                    external_links = [Link(**link_data) for link_data in links["external"]]
                    links_obj = Links(internal=internal_links, external=external_links)

                    # Create a config object for LinkPreview
                    class TempCrawlerRunConfig:
                        def __init__(self, link_config, score_links):
                            self.link_preview_config = link_config
                            self.score_links = score_links

                    config = TempCrawlerRunConfig(link_preview_config, kwargs.get("score_links", False))

                    # Extract head content (run async operation in sync context)
                    async def extract_links():
                        async with LinkPreview(self.logger) as extractor:
                            return await extractor.extract_link_heads(links_obj, config)

                    # Run the async operation
                    try:
                        # Check if we're already in an async context
                        loop = asyncio.get_running_loop()
                        # If we're in an async context, we need to run in a thread
                        import concurrent.futures
                        with concurrent.futures.ThreadPoolExecutor() as executor:
                            future = executor.submit(asyncio.run, extract_links())
                            updated_links = future.result()
                    except RuntimeError:
                        # No running loop, we can use asyncio.run directly
                        updated_links = asyncio.run(extract_links())

                    # Convert back to dict format
                    links["internal"] = [link.dict() for link in updated_links.internal]
                    links["external"] = [link.dict() for link in updated_links.external]

                    if verbose:
                        successful_internal = len([l for l in updated_links.internal if l.head_extraction_status == "valid"])
                        successful_external = len([l for l in updated_links.external if l.head_extraction_status == "valid"])
                        self._log("info", "Link head extraction completed: {internal_success}/{internal_total} internal, {external_success}/{external_total} external",
                                  params={
                                      "internal_success": successful_internal,
                                      "internal_total": len(updated_links.internal),
                                      "external_success": successful_external,
                                      "external_total": len(updated_links.external)
                                  }, tag="LINK_EXTRACT")
                    else:
                        self._log("info", "Link head extraction completed successfully", tag="LINK_EXTRACT")

                except Exception as e:
                    self._log("error", f"Error during link head extraction: {str(e)}", tag="LINK_EXTRACT")
                    # Continue with original links if head extraction fails

            return {
                "cleaned_html": cleaned_html,
                "success": success,
                "media": media,
                "links": links,
                "metadata": meta,
            }

        except Exception as e:
            self._log("error", f"Error processing HTML: {str(e)}", "SCRAPE")
            # Create error message in case of failure
            error_body = lhtml.Element("div")
            # Use etree.SubElement rather than lhtml.SubElement
            error_div = etree.SubElement(error_body, "div", id="crawl4ai_error_message")
            error_div.text = f"""
            Crawl4AI Error: This page is not fully supported.

            Error Message: {str(e)}

            Possible reasons:
            1. The page may have restrictions that prevent crawling.
            2. The page might not be fully loaded.

            Suggestions:
            - Try calling the crawl function with these parameters:
            magic=True,
            - Set headless=False to visualize what's happening on the page.

            If the issue persists, please check the page's structure and any potential anti-crawling measures.
            """
            cleaned_html = lhtml.tostring(
                error_body, encoding="unicode", pretty_print=True
            )
            return {
                "cleaned_html": cleaned_html,
                "success": False,
                "media": {
                    "images": [],
                    "videos": [],
                    "audios": [],
                    "tables": []
                },
                "links": {"internal": [], "external": []},
                "metadata": {},
            }