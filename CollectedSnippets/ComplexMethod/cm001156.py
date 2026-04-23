def validate_cors_allow_origins(cls, v: List[str]) -> List[str]:
        validated: List[str] = []
        localhost_ports: set[str] = set()
        ip127_ports: set[str] = set()

        for raw_origin in v:
            origin = raw_origin.strip()
            if origin.startswith("regex:"):
                pattern = origin[len("regex:") :]
                if not pattern:
                    raise ValueError("Invalid regex pattern: pattern cannot be empty")
                try:
                    re.compile(pattern)
                except re.error as exc:
                    raise ValueError(
                        f"Invalid regex pattern '{pattern}': {exc}"
                    ) from exc
                validated.append(origin)
                continue

            if origin.startswith(("http://", "https://")):
                if "localhost" in origin:
                    try:
                        port = origin.split(":")[2]
                        localhost_ports.add(port)
                    except IndexError as exc:
                        raise ValueError(
                            "localhost origins must include an explicit port, e.g. http://localhost:3000"
                        ) from exc
                if "127.0.0.1" in origin:
                    try:
                        port = origin.split(":")[2]
                        ip127_ports.add(port)
                    except IndexError as exc:
                        raise ValueError(
                            "127.0.0.1 origins must include an explicit port, e.g. http://127.0.0.1:3000"
                        ) from exc
                validated.append(origin)
                continue

            raise ValueError(f"Invalid URL or regex origin: {origin}")

        for port in ip127_ports - localhost_ports:
            validated.append(f"http://localhost:{port}")
        for port in localhost_ports - ip127_ports:
            validated.append(f"http://127.0.0.1:{port}")

        return validated