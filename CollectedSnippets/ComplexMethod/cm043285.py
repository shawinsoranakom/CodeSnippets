async def _generate_media_from_html(
        self, html: str, config: CrawlerRunConfig = None
    ) -> tuple:
        """
        Generate media (screenshot, PDF, MHTML) from raw HTML content.

        This method is used for raw: and file:// URLs where we have HTML content
        but need to render it in a browser to generate media outputs.

        Args:
            html (str): The raw HTML content to render
            config (CrawlerRunConfig, optional): Configuration for media options

        Returns:
            tuple: (screenshot_data, pdf_data, mhtml_data) - any can be None
        """
        page = None
        screenshot_data = None
        pdf_data = None
        mhtml_data = None

        try:
            # Get a browser page
            config = config or CrawlerRunConfig()
            page, context = await self.browser_manager.get_page(crawlerRunConfig=config)

            # Load the HTML content into the page
            await page.set_content(html, wait_until="domcontentloaded")

            # Generate requested media
            if config.pdf:
                pdf_data = await self.export_pdf(page)

            if config.capture_mhtml:
                mhtml_data = await self.capture_mhtml(page)

            if config.screenshot:
                if config.screenshot_wait_for:
                    await asyncio.sleep(config.screenshot_wait_for)
                screenshot_height_threshold = getattr(config, 'screenshot_height_threshold', None)
                screenshot_data = await self.take_screenshot(
                    page,
                    screenshot_height_threshold=screenshot_height_threshold,
                    scan_full_page=getattr(config, 'scan_full_page', True),
                    scroll_delay=config.scroll_delay if config else 0.2
                )

            return screenshot_data, pdf_data, mhtml_data

        except Exception as e:
            error_message = f"Failed to generate media from HTML: {str(e)}"
            self.logger.error(
                message="HTML media generation failed: {error}",
                tag="ERROR",
                params={"error": error_message},
            )
            # Return error image for screenshot if it was requested
            if config and config.screenshot:
                img = Image.new("RGB", (800, 600), color="black")
                draw = ImageDraw.Draw(img)
                font = ImageFont.load_default()
                draw.text((10, 10), error_message, fill=(255, 255, 255), font=font)
                buffered = BytesIO()
                img.save(buffered, format="JPEG")
                screenshot_data = base64.b64encode(buffered.getvalue()).decode("utf-8")
            return screenshot_data, pdf_data, mhtml_data
        finally:
            # Clean up the page
            if page:
                try:
                    await self.browser_manager.release_page_with_context(page)
                    await page.close()
                except Exception:
                    pass