def _format_network_debug_report(max_requests: int = 20, max_routes: int = 10) -> str:
    report = _get_network_debug_report()
    if report["total_requests"] == 0:
        return "Network debug report: no httpx requests captured."

    lines = [
        "Network debug report",
        f"Requests captured: {report['total_requests']}",
        f"Failed requests: {report['failed_requests']}",
        f"Cumulative request time: {report['total_time_ms']:.1f} ms",
    ]

    if report["phase_totals_ms"]:
        phase_summary = ", ".join(
            f"{phase}={duration_ms:.1f} ms"
            for phase, duration_ms in sorted(report["phase_totals_ms"].items(), key=lambda item: item[1], reverse=True)
        )
        lines.append(f"Phase totals: {phase_summary}")

    lines.append("")
    lines.append("Slowest requests:")
    for idx, record in enumerate(
        sorted(report["requests"], key=lambda request: request["total_ms"], reverse=True)[:max_requests],
        start=1,
    ):
        status = record["error"] or f"status={record['status_code']}"
        phase_bits = []
        for phase in ("connect_tcp", "start_tls", "receive_response_headers", "receive_response_body"):
            duration_ms = record["phases_ms"].get(phase)
            if duration_ms is not None:
                phase_bits.append(f"{phase}={duration_ms:.1f} ms")
        phase_suffix = f" ({', '.join(phase_bits)})" if phase_bits else ""
        incomplete_suffix = " incomplete" if record["stream"] and not record["response_complete"] else ""
        lines.append(
            f"{idx:>2}. {record['method']} {record['url']} {record['total_ms']:.1f} ms {status}{incomplete_suffix}{phase_suffix}"
        )

    lines.append("")
    lines.append("Slowest routes:")
    for idx, route in enumerate(report["routes"][:max_routes], start=1):
        lines.append(
            f"{idx:>2}. {route['method']} {route['host_display']}{route['path']} count={route['count']} "
            f"total={route['total_ms']:.1f} ms avg={route['avg_ms']:.1f} ms failures={route['failures']}"
        )

    return "\n".join(lines)