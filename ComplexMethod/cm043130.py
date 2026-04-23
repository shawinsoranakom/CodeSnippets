def parse_markdown_to_cells(markdown_content):
    """Parse markdown content and convert to notebook cells"""
    cells = []

    # Split content by cell markers
    lines = markdown_content.split('\n')

    # Extract the header content before first cell marker
    header_lines = []
    i = 0
    while i < len(lines) and not lines[i].startswith('# cell'):
        header_lines.append(lines[i])
        i += 1

    # Add header as markdown cell if it exists
    if header_lines:
        header_content = '\n'.join(header_lines).strip()
        if header_content:
            cells.append({
                "cell_type": "markdown",
                "metadata": {},
                "source": header_content.split('\n')
            })

    # Process cells marked with # cell X type:Y
    current_cell_content = []
    current_cell_type = None

    while i < len(lines):
        line = lines[i]

        # Check for cell marker
        cell_match = re.match(r'^# cell (\d+) type:(markdown|code)$', line)

        if cell_match:
            # Save previous cell if exists
            if current_cell_content and current_cell_type:
                content = '\n'.join(current_cell_content).strip()
                if content:
                    if current_cell_type == 'code':
                        cells.append({
                            "cell_type": "code",
                            "execution_count": None,
                            "metadata": {},
                            "outputs": [],
                            "source": content.split('\n')
                        })
                    else:
                        cells.append({
                            "cell_type": "markdown",
                            "metadata": {},
                            "source": content.split('\n')
                        })

            # Start new cell
            current_cell_type = cell_match.group(2)
            current_cell_content = []
        else:
            # Add line to current cell
            current_cell_content.append(line)

        i += 1

    # Add last cell if exists
    if current_cell_content and current_cell_type:
        content = '\n'.join(current_cell_content).strip()
        if content:
            if current_cell_type == 'code':
                cells.append({
                    "cell_type": "code",
                    "execution_count": None,
                    "metadata": {},
                    "outputs": [],
                    "source": content.split('\n')
                })
            else:
                cells.append({
                    "cell_type": "markdown",
                    "metadata": {},
                    "source": content.split('\n')
                })

    return cells