def construct(sequence: list[int], n_actions: int):
        if n_actions == max_length:
            scenarios.append(sequence + [0])
            return

        max_number = 0
        present_numbers = set()
        for number in sequence:
            max_number = max(max_number, abs(number))
            if number > 0:
                present_numbers.add(number)
            elif number < 0:
                present_numbers.remove(-number)

        # Add a totally new object. It is possible if it doesn't exceed the files limit.
        if max_number + 1 <= max_files:
            construct(sequence + [max_number + 1], n_actions + 1)

        # Update the state of something that was not touched in the current transaction:
        # either upsert an object (add it if it wasn't present or modify if it was), or
        # delete it.
        for number in range(max_number):
            candidate = number + 1
            if len(sequence) > 0 and candidate <= abs(sequence[-1]):
                # To exclude duplicates, we consider only increasing sequences of ids
                # within a single run of a Pathway program
                continue

            # Upsert an object. This is possible either if replacements are allowed or
            # if there is no such object.
            if allow_replacements or candidate not in present_numbers:
                construct(sequence + [candidate], n_actions + 1)

            # Remove an object. It's possible if it's present.
            if candidate in present_numbers:
                construct(sequence + [-candidate], n_actions + 1)

        # Don't add anything, but mark that the next action will go in the next pw run
        if len(sequence) > 0 and sequence[-1] != 0:
            construct(sequence + [0], n_actions)