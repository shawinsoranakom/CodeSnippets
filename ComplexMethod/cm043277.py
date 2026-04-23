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

        # Reset downloaded files list for new crawl
        self._downloaded_files = []

        # Initialize capture lists
        captured_requests = []
        captured_console = []

        # Handle user agent with magic mode
        user_agent_to_override = config.user_agent
        if user_agent_to_override:
            self.browser_config.user_agent = user_agent_to_override
        elif config.magic or config.user_agent_mode == "random":
            self.browser_config.user_agent = ValidUAGenerator().generate(
                **(config.user_agent_generator_config or {})
            )

        # Get page for session
        page, context = await self.browser_manager.get_page(crawlerRunConfig=config)

        # await page.goto(URL)

        # Add default cookie
        # await context.add_cookies(
        #     [{"name": "cookiesEnabled", "value": "true", "url": url}]
        # )

        # Handle navigator overrides
        if config.override_navigator or config.simulate_user or config.magic:
            await context.add_init_script(load_js_script("navigator_overrider"))

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
        if config.capture_console_messages:
            def handle_console_capture(msg):
                try:
                    message_type = "unknown"
                    try:
                        message_type = msg.type
                    except:
                        pass

                    message_text = "unknown"
                    try:
                        message_text = msg.text
                    except:
                        pass

                    # Basic console message with minimal content
                    entry = {
                        "type": message_type,
                        "text": message_text,
                        "timestamp": time.time()
                    }

                    captured_console.append(entry)

                except Exception as e:
                    if self.logger:
                        self.logger.warning(f"Error capturing console message: {e}", tag="CAPTURE")
                    # Still add something to the list even on error
                    captured_console.append({
                        "type": "console_capture_error", 
                        "error": str(e), 
                        "timestamp": time.time()
                    })

            def handle_pageerror_capture(err):
                try:
                    error_message = "Unknown error"
                    try:
                        error_message = err.message
                    except:
                        pass

                    error_stack = ""
                    try:
                        error_stack = err.stack
                    except:
                        pass

                    captured_console.append({
                        "type": "error",
                        "text": error_message,
                        "stack": error_stack,
                        "timestamp": time.time()
                    })
                except Exception as e:
                    if self.logger:
                        self.logger.warning(f"Error capturing page error: {e}", tag="CAPTURE")
                    captured_console.append({
                        "type": "pageerror_capture_error", 
                        "error": str(e), 
                        "timestamp": time.time()
                    })

            # Add event listeners directly
            page.on("console", handle_console_capture)
            page.on("pageerror", handle_pageerror_capture)

        # Set up console logging if requested
        if config.log_console:
            def log_consol(
                msg, console_log_type="debug"
            ):  # Corrected the parameter syntax
                if console_log_type == "error":
                    self.logger.error(
                        message=f"Console error: {msg}",  # Use f-string for variable interpolation
                        tag="CONSOLE"
                    )
                elif console_log_type == "debug":
                    self.logger.debug(
                        message=f"Console: {msg}",  # Use f-string for variable interpolation
                        tag="CONSOLE"
                    )

            page.on("console", log_consol)
            page.on("pageerror", lambda e: log_consol(e, "error"))

        try:
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

                await self.execute_hook(
                    "after_goto", page, context=context, url=url, response=response, config=config
                )

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
                # if response is None:
                #     status_code = 200
                #     response_headers = {}
                # else:
                #     status_code = response.status
                #     response_headers = response.headers

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
                except Exception as e:
                    self.logger.warning(
                        message="Failed to adjust viewport to content: {error}",
                        tag="VIEWPORT",
                        params={"error": str(e)},
                    )

            # Handle full page scanning
            if config.scan_full_page:
                # await self._handle_full_page_scan(page, config.scroll_delay)
                await self._handle_full_page_scan(page, config.scroll_delay, config.max_scroll_steps)

            # Handle virtual scroll if configured
            if config.virtual_scroll_config:
                await self._handle_virtual_scroll(page, config.virtual_scroll_config)

            # Execute JavaScript if provided
            # if config.js_code:
            #     if isinstance(config.js_code, str):
            #         await page.evaluate(config.js_code)
            #     elif isinstance(config.js_code, list):
            #         for js in config.js_code:
            #             await page.evaluate(js)

            if config.js_code:
                # execution_result = await self.execute_user_script(page, config.js_code)
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

            # Handle user simulation
            if config.simulate_user or config.magic:
                await page.mouse.move(100, 100)
                await page.mouse.down()
                await page.mouse.up()
                await page.keyboard.press("ArrowDown")

            # Handle wait_for condition
            # Todo: Decide how to handle this
            if not config.wait_for and config.css_selector and False:
            # if not config.wait_for and config.css_selector:
                config.wait_for = f"css:{config.css_selector}"

            if config.wait_for:
                try:
                    # Use wait_for_timeout if specified, otherwise fall back to page_timeout
                    timeout = config.wait_for_timeout if config.wait_for_timeout is not None else config.page_timeout
                    await self.smart_wait(
                        page, config.wait_for, timeout=timeout
                    )
                except Exception as e:
                    raise RuntimeError(f"Wait condition failed: {str(e)}")

            # Update image dimensions if needed
            if not self.browser_config.text_mode:
                update_image_dimensions_js = load_js_script("update_image_dimensions")
                try:
                    try:
                        await page.wait_for_load_state("domcontentloaded", timeout=5)
                    except PlaywrightTimeoutError:
                        pass
                    await page.evaluate(update_image_dimensions_js)
                except Exception as e:
                    self.logger.error(
                        message="Error updating image dimensions: {error}",
                        tag="ERROR",
                        params={"error": str(e)},
                    )

            # Process iframes if needed
            if config.process_iframes:
                page = await self.process_iframes(page)

            # Pre-content retrieval hooks and delay
            await self.execute_hook("before_retrieve_html", page, context=context, config=config)
            if config.delay_before_return_html:
                await asyncio.sleep(config.delay_before_return_html)

            # Handle overlay removal
            if config.remove_overlay_elements:
                await self.remove_overlay_elements(page)

            if config.css_selector:
                try:
                    # Handle comma-separated selectors by splitting them
                    selectors = [s.strip() for s in config.css_selector.split(',')]
                    html_parts = []

                    for selector in selectors:
                        try:
                            content = await page.evaluate(
                                f"""Array.from(document.querySelectorAll("{selector}"))
                                    .map(el => el.outerHTML)
                                    .join('')"""
                            )
                            html_parts.append(content)
                        except Error as e:
                            print(f"Warning: Could not get content for selector '{selector}': {str(e)}")

                    # Wrap in a div to create a valid HTML structure
                    html = f"<div class='crawl4ai-result'>\n" + "\n".join(html_parts) + "\n</div>"                    
                except Error as e:
                    raise RuntimeError(f"Failed to extract HTML content: {str(e)}")
            else:
                html = await page.content()

            # # Get final HTML content
            # html = await page.content()
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
                    page, screenshot_height_threshold=config.screenshot_height_threshold
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
                # Include captured data if enabled
                network_requests=captured_requests if config.capture_network_requests else None,
                console_messages=captured_console if config.capture_console_messages else None,
            )

        except Exception as e:
            raise e

        finally:
            # If no session_id is given we should close the page
            all_contexts = page.context.browser.contexts
            total_pages = sum(len(context.pages) for context in all_contexts)                
            if config.session_id:
                pass
            elif total_pages <= 1 and (self.browser_config.use_managed_browser or self.browser_config.headless):
                pass
            else:
                # Detach listeners before closing to prevent potential errors during close
                if config.capture_network_requests:
                    page.remove_listener("request", handle_request_capture)
                    page.remove_listener("response", handle_response_capture)
                    page.remove_listener("requestfailed", handle_request_failed_capture)
                if config.capture_console_messages:
                    page.remove_listener("console", handle_console_capture)
                    page.remove_listener("pageerror", handle_pageerror_capture)

                # Close the page
                await page.close()