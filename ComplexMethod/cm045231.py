async def on_reset(self, cancellation_token: CancellationToken) -> None:
        if not self.did_lazy_init:
            return
        assert self._page is not None

        self._chat_history.clear()
        reset_prior_metadata, reset_last_download = await self._playwright_controller.visit_page(
            self._page, self.start_page
        )
        if reset_last_download and self._last_download is not None:
            self._last_download = None
        if reset_prior_metadata and self._prior_metadata_hash is not None:
            self._prior_metadata_hash = None
        if self.to_save_screenshots:
            current_timestamp = "_" + int(time.time()).__str__()
            screenshot_png_name = "screenshot" + current_timestamp + ".png"

            await self._page.screenshot(path=os.path.join(self.debug_dir, screenshot_png_name))  # type: ignore
            self.logger.info(
                WebSurferEvent(
                    source=self.name,
                    url=self._page.url,
                    message="Screenshot: " + screenshot_png_name,
                )
            )

        self.logger.info(
            WebSurferEvent(
                source=self.name,
                url=self._page.url,
                message="Resetting browser.",
            )
        )