async def get_connection(self):
        """Connection pool manager with enhanced error handling"""
        if not self._initialized:
            async with self.init_lock:
                if not self._initialized:
                    try:
                        await self.initialize()
                        self._initialized = True
                    except Exception as e:
                        import sys

                        error_context = get_error_context(sys.exc_info())
                        self.logger.error(
                            message="Database initialization failed:\n{error}\n\nContext:\n{context}\n\nTraceback:\n{traceback}",
                            tag="ERROR",
                            force_verbose=True,
                            params={
                                "error": str(e),
                                "context": error_context["code_context"],
                                "traceback": error_context["full_traceback"],
                            },
                        )
                        raise

        await self.connection_semaphore.acquire()
        task_id = id(asyncio.current_task())

        try:
            async with self.pool_lock:
                if task_id not in self.connection_pool:
                    try:
                        conn = await aiosqlite.connect(self.db_path, timeout=30.0)
                        await conn.execute("PRAGMA journal_mode = WAL")
                        await conn.execute("PRAGMA busy_timeout = 5000")

                        # Verify database structure
                        async with conn.execute(
                            "PRAGMA table_info(crawled_data)"
                        ) as cursor:
                            columns = await cursor.fetchall()
                            column_names = [col[1] for col in columns]
                            expected_columns = {
                                "url",
                                "html",
                                "cleaned_html",
                                "markdown",
                                "extracted_content",
                                "success",
                                "media",
                                "links",
                                "metadata",
                                "screenshot",
                                "response_headers",
                                "downloaded_files",
                            }
                            missing_columns = expected_columns - set(column_names)
                            if missing_columns:
                                raise ValueError(
                                    f"Database missing columns: {missing_columns}"
                                )

                        self.connection_pool[task_id] = conn
                    except Exception as e:
                        import sys

                        error_context = get_error_context(sys.exc_info())
                        error_message = (
                            f"Unexpected error in db get_connection at line {error_context['line_no']} "
                            f"in {error_context['function']} ({error_context['filename']}):\n"
                            f"Error: {str(e)}\n\n"
                            f"Code context:\n{error_context['code_context']}"
                        )
                        self.logger.error(
                            message="{error}",
                            tag="ERROR",
                            params={"error": str(error_message)},
                            boxes=["error"],
                        )

                        raise

            yield self.connection_pool[task_id]

        except Exception as e:
            import sys

            error_context = get_error_context(sys.exc_info())
            error_message = (
                f"Unexpected error in db get_connection at line {error_context['line_no']} "
                f"in {error_context['function']} ({error_context['filename']}):\n"
                f"Error: {str(e)}\n\n"
                f"Code context:\n{error_context['code_context']}"
            )
            self.logger.error(
                message="{error}",
                tag="ERROR",
                params={"error": str(error_message)},
                boxes=["error"],
            )
            raise
        finally:
            async with self.pool_lock:
                if task_id in self.connection_pool:
                    await self.connection_pool[task_id].close()
                    del self.connection_pool[task_id]
            self.connection_semaphore.release()