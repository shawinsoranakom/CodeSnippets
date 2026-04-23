def _generate_recommendations(self, signals: List[Dict]) -> List[str]:
        """Generate actionable recommendations from signal analysis."""
        recommendations = []

        critical = [
            s
            for s in signals
            if s.get("risk", {}).get("risk_level") == "CRITICAL"
        ]
        if critical:
            recommendations.append(
                f"🚨 Review {len(critical)} critical-risk signals immediately"
            )

        high_rel = [
            s for s in signals if s.get("relevance", {}).get("score", 0) >= 80
        ]
        if high_rel:
            recommendations.append(
                f"📌 Prioritize {len(high_rel)} high-relevance items"
            )

        github = [s for s in signals if s.get("source") == "github"]
        if github:
            recommendations.append(
                f"⭐ Explore {len(github)} trending repositories"
            )

        if not recommendations:
            recommendations.append("✅ No urgent actions required")

        return recommendations