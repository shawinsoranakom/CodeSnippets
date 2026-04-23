def _generate_summary(self, signals: List[Dict]) -> str:
        """Generate executive summary from processed signals."""
        if not signals:
            return "No signals to summarize."

        high_priority = [
            s for s in signals if s.get("relevance", {}).get("score", 0) >= 70
        ]
        critical_risks = [
            s
            for s in signals
            if s.get("risk", {}).get("risk_level") in ["HIGH", "CRITICAL"]
        ]

        parts = [f"Analyzed {len(signals)} signals."]

        if high_priority:
            parts.append(f"{len(high_priority)} high-relevance items detected.")
        if critical_risks:
            parts.append(
                f"⚠️ {len(critical_risks)} signals with elevated risk."
            )
        if signals:
            parts.append(f"Top signal: {signals[0].get('title', 'Unknown')}")

        return " ".join(parts)