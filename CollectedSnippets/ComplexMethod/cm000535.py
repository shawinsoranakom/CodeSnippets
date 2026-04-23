async def run(
        self,
        input_data: Input,
        *,
        credentials: DatabaseCredentials,
        **_kwargs: Any,
    ) -> BlockOutput:
        # Validate query structure and read-only constraints.
        error = self._validate_query(input_data)
        if error:
            yield "error", error
            return

        # Validate host and resolve for SSRF protection.
        host, pinned_host, error = await self._resolve_host(input_data)
        if error:
            yield "error", error
            return

        # Build connection URL and execute.
        port = input_data.port or _DATABASE_TYPE_DEFAULT_PORT[input_data.database_type]
        username = credentials.username.get_secret_value()
        connection_url = URL.create(
            drivername=_DATABASE_TYPE_TO_DRIVER[input_data.database_type],
            username=username,
            password=credentials.password.get_secret_value(),
            host=pinned_host,
            port=port,
            database=input_data.database,
        )
        conn_str = connection_url.render_as_string(hide_password=True)
        db_name = input_data.database

        def _sanitize(err: Exception) -> str:
            return _sanitize_error(
                str(err).strip(),
                conn_str,
                host=pinned_host,
                original_host=host,
                username=username,
                port=port,
                database=db_name,
            )

        try:
            results, columns, affected, truncated = await asyncio.to_thread(
                self.execute_query,
                connection_url=connection_url,
                query=input_data.query,
                timeout=input_data.timeout,
                max_rows=input_data.max_rows,
                read_only=input_data.read_only,
                database_type=input_data.database_type,
            )
            yield "results", results
            yield "columns", columns
            yield "row_count", len(results)
            yield "truncated", truncated
            if affected >= 0:
                yield "affected_rows", affected
        except OperationalError as e:
            yield (
                "error",
                self._classify_operational_error(
                    _sanitize(e),
                    input_data.timeout,
                ),
            )
        except ProgrammingError as e:
            yield "error", f"SQL error: {_sanitize(e)}"
        except DBAPIError as e:
            yield "error", f"Database error: {_sanitize(e)}"
        except ModuleNotFoundError:
            yield (
                "error",
                (
                    f"Database driver not available for "
                    f"{input_data.database_type.value}. "
                    f"Please contact the platform administrator."
                ),
            )