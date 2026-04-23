async def _crawl_web(
        self, url: str, config: CrawlerRunConfig
    ) -> AsyncCrawlResponse:
        """
        Internal method to crawl web URLs with the specified configuration.
        Includes optional network and console capturing.

        Args:
            url (str): The web URL to crawl
            config (CrawlerRunConfig): Configuration object controlling the crawl behavior

        Returns:
            AsyncCrawlResponse: The response containing HTML, headers, status code, and optional data
        """
        config.url = url
        response_headers = {}
        execution_result = None
        status_code = None
        redirected_url = url
        redirected_status_code = None

        # Reset downloaded files list for new crawl
        self._downloaded_files = []

        # Initialize capture lists
        captured_requests = []
        captured_console = []

        # Handle user agent with magic mode.
        # For persistent contexts the UA is locked at browser launch time
        # (launch_persistent_context bakes it into the protocol layer), so
        # changing it here would only desync browser_config from reality.
        # Users should set user_agent or user_agent_mode on BrowserConfig.
        ua_changed = False
        if not self.browser_config.use_persistent_context:
            user_agent_to_override = config.user_agent
            if user_agent_to_override:
                self.browser_config.user_agent = user_agent_to_override
                ua_changed = True
            elif config.magic or config.user_agent_mode == "random":
                self.browser_config.user_agent = ValidUAGenerator().generate(
                    **(config.user_agent_generator_config or {})
                )
                ua_changed = True

        # Keep sec-ch-ua in sync whenever the UA changed
        if ua_changed:
            self.browser_config.browser_hint = UAGen.generate_client_hints(
                self.browser_config.user_agent
            )
            self.browser_config.headers["sec-ch-ua"] = self.browser_config.browser_hint

        # Get page for session
        page, context = await self.browser_manager.get_page(crawlerRunConfig=config)

        # When reusing a session page, abort any pending loads from the
        # previous navigation to prevent timeouts on the next goto().
        if config.session_id:
            try:
                await page.evaluate("window.stop()")
            except Exception:
                pass

        try:
            # Push updated UA + sec-ch-ua to the page so the server sees them
            if ua_changed:
                combined_headers = {
                    "User-Agent": self.browser_config.user_agent,
                    "sec-ch-ua": self.browser_config.browser_hint,
                }
                combined_headers.update(self.browser_config.headers)
                await page.set_extra_http_headers(combined_headers)

            # await page.goto(URL)

            # Add default cookie
            # await context.add_cookies(
            #     [{"name": "cookiesEnabled", "value": "true", "url": url}]
            # )

            # Handle navigator overrides — only inject if not already done
            # at context level by setup_context(). This fallback covers
            # managed-browser / persistent / CDP paths where setup_context()
            # is called without a crawlerRunConfig.
            if config.override_navigator or config.simulate_user or config.magic:
                if not getattr(context, '_crawl4ai_nav_overrider_injected', False):
                    await context.add_init_script(load_js_script("navigator_overrider"))
                    context._crawl4ai_nav_overrider_injected = True

            # Force-open closed shadow roots — same guard against duplication
            if config.flatten_shadow_dom:
                if not getattr(context, '_crawl4ai_shadow_dom_injected', False):
                    await context.add_init_script("""
                        const _origAttachShadow = Element.prototype.attachShadow;
                        Element.prototype.attachShadow = function(init) {
                            return _origAttachShadow.call(this, {...init, mode: 'open'});
                        };
                    """)
                    context._crawl4ai_shadow_dom_injected = True

            # Call hook after page creation
            await self.execute_hook("on_page_context_created", page, context=context, config=config)

            # Network Request Capturing
            if config.capture_network_requests:
                async def handle_request_capture(request):
                    try:
                        post_data_str = None
                        try:
                            # Be cautious with large post data
                            post_data = request.post_data_buffer
                            if post_data:
                                 # Attempt to decode, fallback to base64 or size indication
                                 try:
                                     post_data_str = post_data.decode('utf-8', errors='replace')
                                 except UnicodeDecodeError:
                                     post_data_str = f"[Binary data: {len(post_data)} bytes]"
                        except Exception:
                            post_data_str = "[Error retrieving post data]"

                        captured_requests.append({
                            "event_type": "request",
                            "url": request.url,
                            "method": request.method,
                            "headers": dict(request.headers), # Convert Header dict
                            "post_data": post_data_str,
                            "resource_type": request.resource_type,
                            "is_navigation_request": request.is_navigation_request(),
                            "timestamp": time.time()
                        })
                    except Exception as e:
                        if self.logger:
                            self.logger.warning(f"Error capturing request details for {request.url}: {e}", tag="CAPTURE")
                        captured_requests.append({"event_type": "request_capture_error", "url": request.url, "error": str(e), "timestamp": time.time()})

                async def handle_response_capture(response):
                    try:
                        try:
                            # body = await response.body()
                            # json_body = await response.json()
                            text_body = await response.text()
                        except Exception as e:
                            body = None
                            # json_body = None
                            # text_body = None
                        captured_requests.append({
                            "event_type": "response",
                            "url": response.url,
                            "status": response.status,
                            "status_text": response.status_text,
                            "headers": dict(response.headers), # Convert Header dict
                            "from_service_worker": response.from_service_worker,
                            "request_timing": response.request.timing, # Detailed timing info
                            "timestamp": time.time(),
                            "body" : {
                                # "raw": body,
                                # "json": json_body,
                                "text": text_body
                            }
                        })
                    except Exception as e:
                        if self.logger:
                            self.logger.warning(f"Error capturing response details for {response.url}: {e}", tag="CAPTURE")
                        captured_requests.append({"event_type": "response_capture_error", "url": response.url, "error": str(e), "timestamp": time.time()})

                async def handle_request_failed_capture(request):
                     try:
                        captured_requests.append({
                            "event_type": "request_failed",
                            "url": request.url,
                            "method": request.method,
                            "resource_type": request.resource_type,
                            "failure_text": str(request.failure) if request.failure else "Unknown failure",
                            "timestamp": time.time()
                        })
                     except Exception as e:
                        if self.logger:
                            self.logger.warning(f"Error capturing request failed details for {request.url}: {e}", tag="CAPTURE")
                        captured_requests.append({"event_type": "request_failed_capture_error", "url": request.url, "error": str(e), "timestamp": time.time()})

                page.on("request", handle_request_capture)
                page.on("response", handle_response_capture)
                page.on("requestfailed", handle_request_failed_capture)

            # Console Message Capturing
            handle_console = None
            handle_error = None
            if config.capture_console_messages:
                # Set up console capture using adapter
                handle_console = await self.adapter.setup_console_capture(page, captured_console)
                handle_error = await self.adapter.setup_error_capture(page, captured_console)

            # Set up console logging if requested
            # Note: For undetected browsers, console logging won't work directly
            # but captured messages can still be logged after retrieval
            # Get SSL certificate information if requested and URL is HTTPS
            ssl_cert = None
            if config.fetch_ssl_certificate:
                ssl_cert = SSLCertificate.from_url(url)

            # Set up download handling
            if self.browser_config.accept_downloads:
                page.on(
                    "download",
                    lambda download: asyncio.create_task(
                        self._handle_download(download)
                    ),
                )

            # Handle page navigation and content loading
            if not config.js_only:
                await self.execute_hook("before_goto", page, context=context, url=url, config=config)

                # Check if this is a file:// or raw: URL that needs set_content() instead of goto()
                is_local_content = url.startswith("file://") or url.startswith("raw://") or url.startswith("raw:")

                if is_local_content:
                    # Load local content using set_content() instead of network navigation
                    if url.startswith("file://"):
                        local_file_path = url[7:]  # Remove 'file://' prefix
                        if not os.path.exists(local_file_path):
                            raise FileNotFoundError(f"Local file not found: {local_file_path}")
                        with open(local_file_path, "r", encoding="utf-8") as f:
                            html_content = f.read()
                    else:
                        # raw:// or raw:
                        html_content = url[6:] if url.startswith("raw://") else url[4:]

                    await page.set_content(html_content, wait_until=config.wait_until)
                    response = None
                    # For raw: URLs, only use base_url if provided; don't fall back to the raw HTML string
                    redirected_url = config.base_url
                    status_code = 200
                    response_headers = {}
                else:
                    # Standard web navigation with goto()
                    try:
                        # Generate a unique nonce for this request
                        if config.experimental.get("use_csp_nonce", False):
                            nonce = hashlib.sha256(os.urandom(32)).hexdigest()

                            # Add CSP headers to the request
                            await page.set_extra_http_headers(
                                {
                                    "Content-Security-Policy": f"default-src 'self'; script-src 'self' 'nonce-{nonce}' 'strict-dynamic'"
                                }
                            )

                        response = await page.goto(
                            url, wait_until=config.wait_until, timeout=config.page_timeout
                        )
                        redirected_url = page.url
                        redirected_status_code = response.status if response else None
                    except Error as e:
                        # Allow navigation to be aborted when downloading files
                        # This is expected behavior for downloads in some browser engines
                        if 'net::ERR_ABORTED' in str(e) and self.browser_config.accept_downloads:
                            self.logger.info(
                                message=f"Navigation aborted, likely due to file download: {url}",
                                tag="GOTO",
                                params={"url": url},
                            )
                            response = None
                        else:
                            raise RuntimeError(f"Failed on navigating ACS-GOTO:\n{str(e)}")

                    # ──────────────────────────────────────────────────────────────
                    # Walk the redirect chain.  Playwright returns only the last
                    # hop, so we trace the `request.redirected_from` links until the
                    # first response that differs from the final one and surface its
                    # status-code.
                    # ──────────────────────────────────────────────────────────────
                    if response is None:
                        status_code = 200
                        response_headers = {}
                    else:
                        first_resp = response
                        req = response.request
                        while req and req.redirected_from:
                            prev_req = req.redirected_from
                            prev_resp = await prev_req.response()
                            if prev_resp:                       # keep earliest
                                first_resp = prev_resp
                            req = prev_req

                        status_code = first_resp.status
                        response_headers = first_resp.headers

                await self.execute_hook(
                    "after_goto", page, context=context, url=url, response=response, config=config
                )

            else:
                status_code = 200
                response_headers = {}

            # Wait for body element and visibility
            try:
                await page.wait_for_selector("body", state="attached", timeout=30000)

                # Use the new check_visibility function with csp_compliant_wait
                is_visible = await self.csp_compliant_wait(
                    page,
                    """() => {
                        const element = document.body;
                        if (!element) return false;
                        const style = window.getComputedStyle(element);
                        const isVisible = style.display !== 'none' && 
                                        style.visibility !== 'hidden' && 
                                        style.opacity !== '0';
                        return isVisible;
                    }""",
                    timeout=30000,
                )

                if not is_visible and not config.ignore_body_visibility:
                    visibility_info = await self.check_visibility(page)
                    raise Error(f"Body element is hidden: {visibility_info}")

            except Error:
                visibility_info = await self.check_visibility(page)

                if self.browser_config.verbose:
                    self.logger.debug(
                        message="Body visibility info: {info}",
                        tag="DEBUG",
                        params={"info": visibility_info},
                    )

                if not config.ignore_body_visibility:
                    raise Error(f"Body element is hidden: {visibility_info}")

            # try:
            #     await page.wait_for_selector("body", state="attached", timeout=30000)

            #     await page.wait_for_function(
            #         """
            #         () => {
            #             const body = document.body;
            #             const style = window.getComputedStyle(body);
            #             return style.display !== 'none' &&
            #                 style.visibility !== 'hidden' &&
            #                 style.opacity !== '0';
            #         }
            #     """,
            #         timeout=30000,
            #     )
            # except Error as e:
            #     visibility_info = await page.evaluate(
            #         """
            #         () => {
            #             const body = document.body;
            #             const style = window.getComputedStyle(body);
            #             return {
            #                 display: style.display,
            #                 visibility: style.visibility,
            #                 opacity: style.opacity,
            #                 hasContent: body.innerHTML.length,
            #                 classList: Array.from(body.classList)
            #             }
            #         }
            #     """
            #     )

            #     if self.config.verbose:
            #         self.logger.debug(
            #             message="Body visibility info: {info}",
            #             tag="DEBUG",
            #             params={"info": visibility_info},
            #         )

            #     if not config.ignore_body_visibility:
            #         raise Error(f"Body element is hidden: {visibility_info}")

            # Handle content loading and viewport adjustment
            if not self.browser_config.text_mode and (
                config.wait_for_images or config.adjust_viewport_to_content
            ):
                await page.wait_for_load_state("domcontentloaded")
                await asyncio.sleep(0.1)

                # Check for image loading with improved error handling
                images_loaded = await self.csp_compliant_wait(
                    page,
                    "() => Array.from(document.getElementsByTagName('img')).every(img => img.complete)",
                    timeout=1000,
                )

                if not images_loaded and self.logger:
                    self.logger.warning(
                        message="Some images failed to load within timeout",
                        tag="SCRAPE",
                    )

            # Adjust viewport if needed
            if not self.browser_config.text_mode and config.adjust_viewport_to_content:
                try:
                    dimensions = await self.get_page_dimensions(page)
                    page_height = dimensions["height"]
                    page_width = dimensions["width"]
                    # page_width = await page.evaluate(
                    #     "document.documentElement.scrollWidth"
                    # )
                    # page_height = await page.evaluate(
                    #     "document.documentElement.scrollHeight"
                    # )

                    target_width = self.browser_config.viewport_width
                    target_height = int(target_width * page_width / page_height * 0.95)
                    await page.set_viewport_size(
                        {"width": target_width, "height": target_height}
                    )

                    scale = min(target_width / page_width, target_height / page_height)
                    cdp = await page.context.new_cdp_session(page)
                    await cdp.send(
                        "Emulation.setDeviceMetricsOverride",
                        {
                            "width": page_width,
                            "height": page_height,
                            "deviceScaleFactor": 1,
                            "mobile": False,
                            "scale": scale,
                        },
                    )
                    await cdp.detach()
                except Exception as e:
                    self.logger.warning(
                        message="Failed to adjust viewport to content: {error}",
                        tag="VIEWPORT",
                        params={"error": str(e)},
                    )

            # Handle full page scanning
            if config.scan_full_page:
                scan_timeout = (config.page_timeout or 30000) / 1000  # ms to seconds
                try:
                    await asyncio.wait_for(
                        self._handle_full_page_scan(page, config.scroll_delay, config.max_scroll_steps),
                        timeout=scan_timeout,
                    )
                except asyncio.TimeoutError:
                    self.logger.warning(
                        message="Full page scan timed out after {timeout}s, continuing with partial scroll",
                        tag="PAGE_SCAN",
                        params={"timeout": scan_timeout},
                    )

            # --- Phase 1: Pre-wait JS and interaction ---

            # Execute js_code_before_wait (for triggering loading that wait_for checks)
            if config.js_code_before_wait:
                bw_result = await self.robust_execute_user_script(
                    page, config.js_code_before_wait
                )
                if not bw_result["success"]:
                    self.logger.warning(
                        message="js_code_before_wait had issues: {error}",
                        tag="JS_EXEC",
                        params={"error": bw_result.get("error")},
                    )

            # Handle user simulation — generate mouse movement and scroll
            # signals that anti-bot systems look for, without firing keyboard
            # events (ArrowDown triggers JS framework navigation) or clicking
            # at fixed positions (may hit buttons/links and navigate away).
            if config.simulate_user or config.magic:
                await page.mouse.move(random.randint(100, 300), random.randint(150, 300))
                await page.mouse.move(random.randint(300, 600), random.randint(200, 400))
                await page.mouse.wheel(0, random.randint(200, 400))

            # --- Phase 2: Wait for page readiness ---

            if config.wait_for:
                try:
                    timeout = config.wait_for_timeout if config.wait_for_timeout is not None else config.page_timeout
                    await self.smart_wait(
                        page, config.wait_for, timeout=timeout
                    )
                except Exception as e:
                    raise RuntimeError(f"Wait condition failed: {str(e)}")

            # Handle virtual scroll if configured (after wait_for so container exists)
            if config.virtual_scroll_config:
                await self._handle_virtual_scroll(page, config.virtual_scroll_config)

            # Pre-content retrieval hooks and delay
            await self.execute_hook("before_retrieve_html", page, context=context, config=config)
            if config.delay_before_return_html:
                await asyncio.sleep(config.delay_before_return_html)

            # --- Phase 3: Post-wait JS (runs on fully-loaded page) ---

            if config.js_code:
                execution_result = await self.robust_execute_user_script(
                    page, config.js_code
                )

                if not execution_result["success"]:
                    self.logger.warning(
                        message="User script execution had issues: {error}",
                        tag="JS_EXEC",
                        params={"error": execution_result.get("error")},
                    )

                await self.execute_hook("on_execution_started", page, context=context, config=config)
                await self.execute_hook("on_execution_ended", page, context=context, config=config, result=execution_result)

            # --- Phase 4: DOM processing before HTML capture ---

            # Update image dimensions if needed
            if not self.browser_config.text_mode:
                update_image_dimensions_js = load_js_script("update_image_dimensions")
                try:
                    try:
                        await page.wait_for_load_state("domcontentloaded", timeout=5)
                    except PlaywrightTimeoutError:
                        pass
                    await self.adapter.evaluate(page, update_image_dimensions_js)
                except Exception as e:
                    self.logger.error(
                        message="Error updating image dimensions: {error}",
                        tag="ERROR",
                        params={"error": str(e)},
                    )

            # Process iframes if needed
            if config.process_iframes:
                page = await self.process_iframes(page)

            # Handle CMP/consent popup removal (before generic overlay removal)
            if config.remove_consent_popups:
                await self.remove_consent_popups(page)

            # Handle overlay removal
            if config.remove_overlay_elements:
                await self.remove_overlay_elements(page)

            # --- Phase 5: HTML capture ---

            if config.flatten_shadow_dom:
                # Use JS to serialize the full DOM including shadow roots
                flatten_js = load_js_script("flatten_shadow_dom")
                html = await self.adapter.evaluate(page, flatten_js)
                if not html or not isinstance(html, str):
                    # Fallback to normal capture if JS returned nothing
                    self.logger.warning(
                        message="Shadow DOM flattening returned no content, falling back to page.content()",
                        tag="SCRAPE",
                    )
                    html = await page.content()
            elif config.css_selector:
                try:
                    selectors = [s.strip() for s in config.css_selector.split(',')]
                    html_parts = []

                    for selector in selectors:
                        try:
                            content = await self.adapter.evaluate(page,
                                f"""Array.from(document.querySelectorAll("{selector}"))
                                    .map(el => el.outerHTML)
                                    .join('')"""
                            )
                            html_parts.append(content)
                        except Error as e:
                            print(f"Warning: Could not get content for selector '{selector}': {str(e)}")

                    html = f"<div class='crawl4ai-result'>\n" + "\n".join(html_parts) + "\n</div>"
                except Error as e:
                    raise RuntimeError(f"Failed to extract HTML content: {str(e)}")
            else:
                html = await page.content()

            await self.execute_hook(
                "before_return_html", page=page, html=html, context=context, config=config
            )

            # Handle PDF, MHTML and screenshot generation
            start_export_time = time.perf_counter()
            pdf_data = None
            screenshot_data = None
            mhtml_data = None

            if config.pdf:
                pdf_data = await self.export_pdf(page)

            if config.capture_mhtml:
                mhtml_data = await self.capture_mhtml(page)

            if config.screenshot:
                if config.screenshot_wait_for:
                    await asyncio.sleep(config.screenshot_wait_for)
                screenshot_data = await self.take_screenshot(
                    page,
                    screenshot_height_threshold=config.screenshot_height_threshold,
                    force_viewport_screenshot=config.force_viewport_screenshot,
                    scan_full_page=config.scan_full_page,
                    scroll_delay=config.scroll_delay
                )

            if screenshot_data or pdf_data or mhtml_data:
                self.logger.info(
                    message="Exporting media (PDF/MHTML/screenshot) took {duration:.2f}s",
                    tag="EXPORT",
                    params={"duration": time.perf_counter() - start_export_time},
                )

            # Define delayed content getter
            async def get_delayed_content(delay: float = 5.0) -> str:
                self.logger.info(
                    message="Waiting for {delay} seconds before retrieving content for {url}",
                    tag="INFO",
                    params={"delay": delay, "url": url},
                )
                await asyncio.sleep(delay)
                return await page.content()

            # For undetected browsers, retrieve console messages before returning
            if config.capture_console_messages and hasattr(self.adapter, 'retrieve_console_messages'):
                final_messages = await self.adapter.retrieve_console_messages(page)
                captured_console.extend(final_messages)

            ###
            # This ensures we capture the current page URL at the time we return the response,
            # which correctly reflects any JavaScript navigation that occurred.
            # For raw:/file:// URLs, preserve the earlier redirected_url (config.base_url or None)
            # instead of using page.url which would be "about:blank".
            ###
            is_local_content = url.startswith("file://") or url.startswith("raw://") or url.startswith("raw:")
            if not is_local_content:
                redirected_url = page.url  # Use current page URL to capture JS redirects

            # Return complete response
            return AsyncCrawlResponse(
                html=html,
                response_headers=response_headers,
                js_execution_result=execution_result,
                status_code=status_code,
                screenshot=screenshot_data,
                pdf_data=pdf_data,
                mhtml_data=mhtml_data,
                get_delayed_content=get_delayed_content,
                ssl_certificate=ssl_cert,
                downloaded_files=(
                    self._downloaded_files if self._downloaded_files else None
                ),
                redirected_url=redirected_url,
                redirected_status_code=redirected_status_code,
                # Include captured data if enabled
                network_requests=captured_requests if config.capture_network_requests else None,
                console_messages=captured_console if config.capture_console_messages else None,
            )

        except Exception as e:
            raise e

        finally:
            # Always clean up event listeners to prevent accumulation
            # across reuses (even for session pages).
            try:
                if config.capture_network_requests:
                    page.remove_listener("request", handle_request_capture)
                    page.remove_listener("response", handle_response_capture)
                    page.remove_listener("requestfailed", handle_request_failed_capture)
                if config.capture_console_messages:
                    if hasattr(self.adapter, 'retrieve_console_messages'):
                        final_messages = await self.adapter.retrieve_console_messages(page)
                        captured_console.extend(final_messages)
                    await self.adapter.cleanup_console_capture(page, handle_console, handle_error)
            except Exception:
                pass

            if not config.session_id:
                # ALWAYS decrement refcount first — must succeed even if
                # the browser crashed or the page is in a bad state.
                try:
                    await self.browser_manager.release_page_with_context(page)
                except Exception:
                    pass

                # Close the page unless it's the last one in a headless/managed browser
                try:
                    all_contexts = page.context.browser.contexts
                    total_pages = sum(len(context.pages) for context in all_contexts)
                    if not (total_pages <= 1 and (self.browser_config.use_managed_browser or self.browser_config.headless)):
                        await page.close()
                except Exception:
                    pass