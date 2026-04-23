def get_prometheus_metrics(server: RemoteOpenAIServer) -> dict[str, dict[str, float]]:
    """Fetch and parse Prometheus metrics from the /metrics endpoint.

    Returns:
        Dict mapping metric names to their values grouped by labels.
        For example: {"vllm:request_success": {
            "engine=0": 5.0, "engine=1": 3.0}
        }
    """
    try:
        response = requests.get(server.url_for("metrics"), timeout=10)
        response.raise_for_status()

        metrics: dict[str, dict[str, float]] = {}

        # Regex patterns for Prometheus metrics
        metric_with_labels = re.compile(
            r"^([a-zA-Z_:][a-zA-Z0-9_:]*)\{([^}]*)\}\s+([\d\.\-\+e]+)$"
        )
        metric_simple = re.compile(r"^([a-zA-Z_:][a-zA-Z0-9_:]*)\s+([\d\.\-\+e]+)$")

        for line in response.text.split("\n"):
            line = line.strip()
            # Skip comments and empty lines
            if not line or line.startswith("#"):
                continue

            # Try to match metric with labels first
            match = metric_with_labels.match(line)
            if match:
                metric_name, labels_part, value_str = match.groups()
                try:
                    value = float(value_str)
                    if metric_name not in metrics:
                        metrics[metric_name] = {}
                    metrics[metric_name][f"{{{labels_part}}}"] = value
                except ValueError:
                    continue
            else:
                # Try simple metric without labels
                match = metric_simple.match(line)
                if match:
                    metric_name, value_str = match.groups()
                    try:
                        value = float(value_str)
                        if metric_name not in metrics:
                            metrics[metric_name] = {}
                        metrics[metric_name][""] = value
                    except ValueError:
                        continue

        return metrics
    except Exception as e:
        pytest.fail(f"Failed to fetch Prometheus metrics: {e}")
        return {}