def _is_same_kind(self) -> int:
        # Kind Values for internal use:
        # 7: Four of a kind
        # 6: Full house
        # 3: Three of a kind
        # 2: Two pairs
        # 1: One pair
        # 0: False
        kind = val1 = val2 = 0
        for i in range(4):
            # Compare two cards at a time, if they are same increase 'kind',
            # add the value of the card to val1, if it is repeating again we
            # will add 2 to 'kind' as there are now 3 cards with same value.
            # If we get card of different value than val1, we will do the same
            # thing with val2
            if self._card_values[i] == self._card_values[i + 1]:
                if not val1:
                    val1 = self._card_values[i]
                    kind += 1
                elif val1 == self._card_values[i]:
                    kind += 2
                elif not val2:
                    val2 = self._card_values[i]
                    kind += 1
                elif val2 == self._card_values[i]:
                    kind += 2
        # For consistency in hand type (look at note in _get_hand_type function)
        kind = kind + 2 if kind in [4, 5] else kind
        # first meaning first pair to compare in 'compare_with'
        first = max(val1, val2)
        second = min(val1, val2)
        # If it's full house (three count pair + two count pair), make sure
        # first pair is three count and if not then switch them both.
        if kind == 6 and self._card_values.count(first) != 3:
            first, second = second, first
        self._first_pair = first
        self._second_pair = second
        return kind