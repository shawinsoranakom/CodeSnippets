async def _run():
            events = []

            events.append({
                "type": "start",
                "data": {
                    "scenario": self.scenario["title"],
                    "item": self.scenario["item"]["name"],
                    "asking_price": self.state.asking_price,
                    "max_rounds": self.max_rounds
                }
            })

            # Initial context for buyer
            buyer_context = "Make your opening offer for this item. Start strong but leave room to negotiate."

            while not self.state.is_complete and self.state.round_count < self.max_rounds:
                round_num = self.state.round_count + 1
                current_round = NegotiationRound(round_number=round_num)

                # Get buyer's offer
                try:
                    buyer_data = await self._get_buyer_offer(buyer_context)
                    current_round.buyer_offer = buyer_data["offer_amount"]
                    current_round.buyer_message = buyer_data["message"]
                    current_round.buyer_reasoning = buyer_data["reasoning"]
                    self.state.current_offer = buyer_data["offer_amount"]

                    events.append({
                        "type": "buyer_offer",
                        "data": {
                            "round": round_num,
                            "offer": buyer_data["offer_amount"],
                            "message": buyer_data["message"],
                            "reasoning": buyer_data["reasoning"],
                            "confidence": buyer_data["confidence"],
                            "willing_to_walk": buyer_data["willing_to_walk"]
                        }
                    })

                except Exception as e:
                    events.append({"type": "error", "data": {"agent": "buyer", "error": str(e)}})
                    break

                # Get seller's response
                try:
                    seller_data = await self._get_seller_response(
                        buyer_data["offer_amount"],
                        buyer_data["message"]
                    )

                    current_round.seller_action = seller_data["action"]
                    current_round.seller_message = seller_data["message"]
                    current_round.seller_reasoning = seller_data["reasoning"]
                    if seller_data["counter_amount"]:
                        current_round.seller_counter = seller_data["counter_amount"]

                    events.append({
                        "type": "seller_response",
                        "data": {
                            "round": round_num,
                            "action": seller_data["action"],
                            "counter": seller_data["counter_amount"],
                            "message": seller_data["message"],
                            "reasoning": seller_data["reasoning"],
                            "firmness": seller_data["firmness"]
                        }
                    })

                    # Handle seller's decision
                    if seller_data["action"] == "accept":
                        self.state.status = "deal"
                        self.state.final_price = buyer_data["offer_amount"]
                        self.state.rounds.append(current_round)

                        events.append({
                            "type": "deal",
                            "data": {
                                "final_price": buyer_data["offer_amount"],
                                "rounds": round_num,
                                "savings": self.state.asking_price - buyer_data["offer_amount"],
                                "percent_off": round((self.state.asking_price - buyer_data["offer_amount"]) / self.state.asking_price * 100, 1)
                            }
                        })
                        break

                    elif seller_data["action"] == "walk":
                        self.state.status = "seller_walked"
                        self.state.rounds.append(current_round)

                        events.append({
                            "type": "walk",
                            "data": {
                                "who": "seller",
                                "round": round_num,
                                "last_offer": buyer_data["offer_amount"]
                            }
                        })
                        break

                    elif seller_data["action"] == "reject":
                        buyer_context = f"Your offer of ${buyer_data['offer_amount']:,} was rejected. The seller said: \"{seller_data['message']}\". Make a new offer or walk away."

                    else:  # counter
                        buyer_context = f"The seller countered with ${seller_data['counter_amount']:,}. They said: \"{seller_data['message']}\". Make your next move."

                except Exception as e:
                    events.append({"type": "error", "data": {"agent": "seller", "error": str(e)}})
                    break

                self.state.rounds.append(current_round)

            # Max rounds reached
            if self.state.status == "ongoing":
                self.state.status = "no_deal"
                events.append({
                    "type": "no_deal",
                    "data": {
                        "reason": "max_rounds",
                        "rounds": self.state.round_count,
                        "last_offer": self.state.current_offer
                    }
                })

            return events