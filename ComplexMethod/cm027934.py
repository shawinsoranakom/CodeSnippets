def get_negotiation_history(self) -> str:
        """Format the negotiation history for agent context."""
        if not self.rounds:
            return "No offers yet. This is the opening round."

        lines = []
        for r in self.rounds:
            lines.append(f"Round {r.round_number}:")
            if r.buyer_offer:
                lines.append(f"  Buyer offered: ${r.buyer_offer:,}")
                lines.append(f"  Buyer said: \"{r.buyer_message}\"")
            if r.seller_action:
                if r.seller_action == "accept":
                    lines.append(f"  Seller ACCEPTED!")
                elif r.seller_action == "counter" and r.seller_counter:
                    lines.append(f"  Seller countered: ${r.seller_counter:,}")
                elif r.seller_action == "reject":
                    lines.append(f"  Seller rejected the offer")
                elif r.seller_action == "walk":
                    lines.append(f"  Seller walked away!")
                if r.seller_message:
                    lines.append(f"  Seller said: \"{r.seller_message}\"")
            lines.append("")

        return "\n".join(lines)