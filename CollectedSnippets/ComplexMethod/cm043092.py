def generate_insights(self, df: pd.DataFrame) -> str:
        """
        Generates a tactical trading report with:
        - Top 3 trades per risk level (High/Medium/Low)
        - Auto-calculated entry/exit prices
        - BTC chart toggle tip
        """
        # Filter top candidates for each risk level
        high_risk = (
            df[df["Undervalued Flag"]]
            .sort_values("Momentum Score", ascending=False)
            .head(3)
        )
        medium_risk = (
            df[df["Liquid Giant"]]
            .sort_values("Volume/Market Cap Ratio", ascending=False)
            .head(3)
        )
        low_risk = (
            df[(df["Momentum Score"] > 0.05) & (df["Volatility Score"] < 0.03)]
            .sort_values("Momentum Score", ascending=False)
            .head(3)
        )

        report = ["# 🎯 Crypto Trading Tactical Report (Top 3 Per Risk Tier)"]

        # 1. High-Risk Trades (Small-Cap Momentum)
        if not high_risk.empty:
            report.append("\n## 🔥 HIGH RISK: Small-Cap Rockets (5-50% Potential)")
            for i, coin in high_risk.iterrows():
                current_price = coin["Price"]
                entry = current_price * 0.95  # -5% dip
                stop_loss = current_price * 0.90  # -10%
                take_profit = current_price * 1.20  # +20%

                report.append(
                    f"\n### {coin['Name']} (Momentum: {coin['Momentum Score']:.1%})"
                    f"\n- **Current Price:** ${current_price:.4f}"
                    f"\n- **Entry:** < ${entry:.4f} (Wait for pullback)"
                    f"\n- **Stop-Loss:** ${stop_loss:.4f} (-10%)"
                    f"\n- **Target:** ${take_profit:.4f} (+20%)"
                    f"\n- **Risk/Reward:** 1:2"
                    f"\n- **Watch:** Volume spikes above {coin['Volume(24h)']/1e6:.1f}M"
                )

        # 2. Medium-Risk Trades (Liquid Giants)
        if not medium_risk.empty:
            report.append("\n## 💎 MEDIUM RISK: Liquid Swing Trades (10-30% Potential)")
            for i, coin in medium_risk.iterrows():
                current_price = coin["Price"]
                entry = current_price * 0.98  # -2% dip
                stop_loss = current_price * 0.94  # -6%
                take_profit = current_price * 1.15  # +15%

                report.append(
                    f"\n### {coin['Name']} (Liquidity Score: {coin['Volume/Market Cap Ratio']:.1%})"
                    f"\n- **Current Price:** ${current_price:.2f}"
                    f"\n- **Entry:** < ${entry:.2f} (Buy slight dips)"
                    f"\n- **Stop-Loss:** ${stop_loss:.2f} (-6%)"
                    f"\n- **Target:** ${take_profit:.2f} (+15%)"
                    f"\n- **Hold Time:** 1-3 weeks"
                    f"\n- **Key Metric:** Volume/Cap > 15%"
                )

        # 3. Low-Risk Trades (Stable Momentum)
        if not low_risk.empty:
            report.append("\n## 🛡️ LOW RISK: Steady Gainers (5-15% Potential)")
            for i, coin in low_risk.iterrows():
                current_price = coin["Price"]
                entry = current_price * 0.99  # -1% dip
                stop_loss = current_price * 0.97  # -3%
                take_profit = current_price * 1.10  # +10%

                report.append(
                    f"\n### {coin['Name']} (Stability Score: {1/coin['Volatility Score']:.1f}x)"
                    f"\n- **Current Price:** ${current_price:.2f}"
                    f"\n- **Entry:** < ${entry:.2f} (Safe zone)"
                    f"\n- **Stop-Loss:** ${stop_loss:.2f} (-3%)"
                    f"\n- **Target:** ${take_profit:.2f} (+10%)"
                    f"\n- **DCA Suggestion:** 3 buys over 72 hours"
                )

        # Volume Anomaly Alert
        anomalies = df[df["Volume Anomaly"]].sort_values("Volume(24h)", ascending=False).head(2)
        if not anomalies.empty:
            report.append("\n⚠️ **Volume Spike Alerts**")
            for i, coin in anomalies.iterrows():
                report.append(
                    f"- {coin['Name']}: Volume {coin['Volume(24h)']/1e6:.1f}M "
                    f"(3x normal) | Price moved: {coin['24h %']:.1%}"
                )

        # Pro Tip
        report.append(
            "\n📊 **Chart Hack:** Hide BTC in visuals:\n"
            "```python\n"
            "# For 3D Map:\n"
            "fig.update_traces(visible=False, selector={'name':'Bitcoin'})\n"
            "# For Treemap:\n"
            "df = df[df['Name'] != 'Bitcoin']\n"
            "```"
        )

        return "\n".join(report)