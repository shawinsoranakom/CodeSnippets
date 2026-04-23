async def fill_form(
        self,
        url: str,
        fields: dict[str, str],
        submit: bool = False,
    ) -> str:
        """Fill form fields on a webpage.

        Args:
            url: The URL of the webpage
            fields: Dict mapping selectors to values
            submit: Whether to submit the form

        Returns:
            Success message with filled fields
        """
        _ensure_playwright_imported()
        page = None
        try:
            page = await self._open_page(url)

            filled = []
            for selector, value in fields.items():
                try:
                    locator = page.locator(selector)
                    await locator.fill(value)
                    filled.append(selector)
                except Exception as e:
                    raise CommandExecutionError(
                        f"Could not fill field '{selector}': {e}"
                    )

            if submit and filled:
                # Try to find and click submit button
                try:
                    submit_btn = page.locator(
                        "button[type='submit'], input[type='submit']"
                    )
                    await submit_btn.click()
                    await self._smart_wait(page)
                except Exception:
                    # Try submitting the form directly
                    try:
                        await page.locator("form").evaluate("form => form.submit()")
                        await self._smart_wait(page)
                    except Exception as e:
                        raise CommandExecutionError(f"Could not submit form: {e}")

            msg = f"Filled {len(filled)} field(s): {', '.join(filled)}"
            if submit:
                msg += " and submitted form"
            return msg

        except CommandExecutionError:
            raise
        except Exception as e:
            raise CommandExecutionError(f"Form fill failed: {e}")
        finally:
            if page:
                await page.close()