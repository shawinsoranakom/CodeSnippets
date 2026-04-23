def parse_axtree_content(content: str) -> dict[str, str]:
    """Parse the accessibility tree content to extract bid -> element description mapping."""
    elements = {}
    current_bid = None
    description_lines = []

    # Find the accessibility tree section
    lines = content.split('\n')
    in_axtree = False

    for line in lines:
        line = line.strip()

        # Check if we're entering the accessibility tree section
        if 'BEGIN accessibility tree' in line:
            in_axtree = True
            continue
        elif 'END accessibility tree' in line:
            break

        if not in_axtree or not line:
            continue

        # Check for bid line format: [bid] element description
        bid_match = re.match(r'\[([a-zA-Z0-9]+)\]\s*(.*)', line)
        if bid_match:
            # Save previous element if it exists
            if current_bid and description_lines:
                elements[current_bid] = ' '.join(description_lines)

            # Start new element
            current_bid = bid_match.group(1)
            description_lines = [bid_match.group(2).strip()]
        else:
            # Add to current description if we have a bid
            if current_bid:
                description_lines.append(line)

    # Save last element
    if current_bid and description_lines:
        elements[current_bid] = ' '.join(description_lines)

    return elements