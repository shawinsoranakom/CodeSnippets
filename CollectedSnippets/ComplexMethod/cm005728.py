def build_report(self) -> dict[str, Any]:
        with self._lock:
            records = [
                {
                    **record,
                    "phases_ms": dict(record["phases_ms"]),
                }
                for record in self._records
            ]

        phase_totals_ms = defaultdict(float)
        route_totals = {}
        for record in records:
            for phase, duration_ms in record["phases_ms"].items():
                phase_totals_ms[phase] += duration_ms

            route_key = (record["method"], record["host_display"], record["path"])
            route_total = route_totals.setdefault(
                route_key,
                {
                    "method": record["method"],
                    "host_display": record["host_display"],
                    "path": record["path"],
                    "count": 0,
                    "failures": 0,
                    "total_ms": 0.0,
                    "phase_totals_ms": defaultdict(float),
                },
            )
            route_total["count"] += 1
            route_total["total_ms"] += record["total_ms"]
            route_total["failures"] += int(record["error"] is not None)
            for phase, duration_ms in record["phases_ms"].items():
                route_total["phase_totals_ms"][phase] += duration_ms

        routes = []
        for route_total in route_totals.values():
            route_total["avg_ms"] = route_total["total_ms"] / route_total["count"]
            route_total["phase_totals_ms"] = dict(sorted(route_total["phase_totals_ms"].items()))
            routes.append(route_total)

        routes.sort(key=lambda route: route["total_ms"], reverse=True)
        total_time_ms = sum(record["total_ms"] for record in records)
        return {
            "enabled": self._enabled,
            "output_path": self._output_path,
            "total_requests": len(records),
            "failed_requests": sum(int(record["error"] is not None) for record in records),
            "total_time_ms": total_time_ms,
            "phase_totals_ms": dict(sorted(phase_totals_ms.items())),
            "requests": records,
            "routes": routes,
        }