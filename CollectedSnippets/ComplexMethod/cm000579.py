def _sanitize_error(
    error_msg: str,
    connection_string: str,
    *,
    host: str = "",
    original_host: str = "",
    username: str = "",
    port: int = 0,
    database: str = "",
) -> str:
    """Remove connection string, credentials, and infrastructure details
    from error messages so they are safe to expose to the LLM.

    Scrubs:
    - The full connection string
    - URL-embedded credentials (``://user:pass@``)
    - ``password=<value>`` key-value pairs
    - The database hostname / IP used for the connection
    - The original (pre-resolution) hostname provided by the user
    - Any IPv4 addresses that appear in the message
    - Any bracketed IPv6 addresses (e.g. ``[::1]``, ``[fe80::1%eth0]``)
    - The database username
    - The database port number
    - The database name
    """
    sanitized = error_msg.replace(connection_string, "<connection_string>")
    sanitized = re.sub(r"password=[^\s&]+", "password=***", sanitized)
    sanitized = re.sub(r"://[^@]+@", "://***:***@", sanitized)

    # Replace the known host (may be an IP already) before the generic IP pass.
    # Also replace the original (pre-DNS-resolution) hostname if it differs.
    if original_host and original_host != host:
        sanitized = sanitized.replace(original_host, "<host>")
    if host:
        sanitized = sanitized.replace(host, "<host>")

    # Replace any remaining IPv4 addresses (e.g. resolved IPs the driver logs)
    sanitized = re.sub(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", "<ip>", sanitized)

    # Replace bracketed IPv6 addresses (e.g. "[::1]", "[fe80::1%eth0]")
    sanitized = re.sub(r"\[[0-9a-fA-F:]+(?:%[^\]]+)?\]", "<ip>", sanitized)

    # Replace the database username (handles double-quoted, single-quoted,
    # and unquoted formats across PostgreSQL, MySQL, and MSSQL error messages).
    if username:
        sanitized = re.sub(
            r"""for user ["']?""" + re.escape(username) + r"""["']?""",
            "for user <user>",
            sanitized,
        )
        # Catch remaining bare occurrences in various quote styles:
        # - PostgreSQL: "FATAL:  role "myuser" does not exist"
        # - MySQL: "Access denied for user 'myuser'@'host'"
        # - MSSQL: "Login failed for user 'myuser'"
        sanitized = sanitized.replace(f'"{username}"', "<user>")
        sanitized = sanitized.replace(f"'{username}'", "<user>")

    # Replace the port number (handles "port 5432" and ":5432" formats)
    if port:
        port_str = re.escape(str(port))
        sanitized = re.sub(
            r"(?:port |:)" + port_str + r"(?![0-9])",
            lambda m: ("port " if m.group().startswith("p") else ":") + "<port>",
            sanitized,
        )

    # Replace the database name to avoid leaking internal infrastructure names.
    # Use word-boundary regex to prevent mangling when the database name is a
    # common substring (e.g. "test", "data", "on").
    if database:
        sanitized = re.sub(r"\b" + re.escape(database) + r"\b", "<database>", sanitized)

    return sanitized