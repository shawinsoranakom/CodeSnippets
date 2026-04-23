async def robust_execute_user_script(
        self, page: Page, js_code: Union[str, List[str]]
    ) -> Dict[str, Any]:
        """
        Executes user-provided JavaScript code with proper error handling and context,
        supporting both synchronous and async user code, plus navigations.

        How it works:
        1. Wait for load state 'domcontentloaded'
        2. If js_code is a string, execute it directly
        3. If js_code is a list, execute each element in sequence
        4. Wait for load state 'networkidle'
        5. Return results

        Args:
            page (Page): The Playwright page instance
            js_code (Union[str, List[str]]): The JavaScript code to execute

        Returns:
            Dict[str, Any]: The results of the execution
        """
        try:
            await page.wait_for_load_state("domcontentloaded")

            if isinstance(js_code, str):
                scripts = [js_code]
            else:
                scripts = js_code

            results = []
            for script in scripts:
                try:
                    # Attempt the evaluate
                    # If the user code triggers navigation, we catch the "context destroyed" error
                    # then wait for the new page to load before continuing
                    result = None
                    try:
                        # OLD VERSION:
                        # result = await page.evaluate(
                        #     f"""
                        # (async () => {{
                        #     try {{
                        #         const script_result = {script};
                        #         return {{ success: true, result: script_result }};
                        #     }} catch (err) {{
                        #         return {{ success: false, error: err.toString(), stack: err.stack }};
                        #     }}
                        # }})();
                        # """
                        # )

                        # """ NEW VERSION:
                        # When {script} contains statements (e.g., const link = …; link.click();), 
                        # this forms invalid JavaScript, causing Playwright execution error: SyntaxError: Unexpected token 'const'.
                        # """
                        result = await self.adapter.evaluate(page,
                            f"""
                        (async () => {{
                            try {{
                                return await (async () => {{
                                    {script}
                                }})();
                            }} catch (err) {{
                                return {{ success: false, error: err.toString(), stack: err.stack }};
                            }}
                        }})();
                        """
                        )
                    except Error as e:
                        # If it's due to navigation destroying the context, handle gracefully
                        if "Execution context was destroyed" in str(e):
                            self.logger.info(
                                "Navigation triggered by script, waiting for load state",
                                tag="JS_EXEC",
                            )
                            try:
                                await page.wait_for_load_state("load", timeout=30000)
                            except Error as nav_err:
                                self.logger.warning(
                                    message="Navigation wait failed: {error}",
                                    tag="JS_EXEC",
                                    params={"error": str(nav_err)},
                                )
                            try:
                                await page.wait_for_load_state(
                                    "networkidle", timeout=30000
                                )
                            except Error as nav_err:
                                self.logger.warning(
                                    message="Network idle wait failed: {error}",
                                    tag="JS_EXEC",
                                    params={"error": str(nav_err)},
                                )
                            # Return partial success, or adapt as you see fit
                            result = {
                                "success": True,
                                "info": "Navigation triggered, ignoring context destroyed error",
                            }
                        else:
                            # It's some other error, log and continue
                            self.logger.error(
                                message="Playwright execution error: {error}",
                                tag="JS_EXEC",
                                params={"error": str(e)},
                            )
                            result = {"success": False, "error": str(e)}

                    # If we made it this far with no repeated error, do post-load waits
                    t1 = time.time()
                    try:
                        await page.wait_for_load_state("domcontentloaded", timeout=5000)
                    except Error as e:
                        self.logger.warning(
                            message="DOM content load timeout: {error}",
                            tag="JS_EXEC",
                            params={"error": str(e)},
                        )

                    # t1 = time.time()
                    # try:
                    #     await page.wait_for_load_state('networkidle', timeout=5000)
                    #     print("Network idle after script execution in", time.time() - t1)
                    # except Error as e:
                    #     self.logger.warning(
                    #         message="Network idle timeout: {error}",
                    #         tag="JS_EXEC",
                    #         params={"error": str(e)}
                    #     )

                    results.append(result if result else {"success": True})

                except Exception as e:
                    # Catch anything else
                    self.logger.error(
                        message="Script chunk failed: {error}",
                        tag="JS_EXEC",
                        params={"error": str(e)},
                    )
                    results.append({"success": False, "error": str(e)})

            return {"success": True, "results": results}

        except Exception as e:
            self.logger.error(
                message="Script execution failed: {error}",
                tag="JS_EXEC",
                params={"error": str(e)},
            )
            return {"success": False, "error": str(e)}