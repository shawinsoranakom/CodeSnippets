def clean_pdf_text(page_number, text):
    # Decode Unicode escapes and handle surrogate pairs
    try:
        decoded = text.encode('latin-1').decode('unicode-escape')
        decoded = decoded.encode('utf-16', 'surrogatepass').decode('utf-16')
    except Exception as e:
        decoded = text  # Fallback if decoding fails

    article_title_detected = False
    decoded = re.sub(r'\.\n', '.\n\n', decoded)
    lines = decoded.split('\n')
    output = []
    current_paragraph = []
    in_header = False
    email_pattern = re.compile(r'\{.*?\}')
    affiliation_pattern = re.compile(r'^†')
    quote_pattern = re.compile(r'^["“]')
    author_pattern = re.compile(
        r'^\s*[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*\s*(?:[†*0-9]+)?'
        r'(?:,\s*[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*\s*(?:[†*0-9]+)?)*'
        r'(?:,\s*(?:and|&)\s+[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*\s*(?:[†*0-9]+)?)?\s*$'
    )

    def flush_paragraph():
        if current_paragraph:
            para = ' '.join(current_paragraph)
            para = re.sub(r'\s+', ' ', para).strip()
            if para:
                output.append(para)
            current_paragraph.clear()

    for i, line in enumerate(lines):
        line = line.strip()

        # Handle special patterns
        if not line:
            flush_paragraph()
            continue

        # Detect headline (first line, reasonable length, surrounded by empty lines)
        if not article_title_detected and i == 0 and 3 <= len(line.split()) <= 8 and (len(lines) > 1):
            flush_paragraph()
            output.append(f'## {line}')
            continue

        # Detect paragraph breaks for ALL paragraphs
        if not line and current_paragraph:
            flush_paragraph()
            output.append('')  # Add empty line between paragraphs
            continue

        # Detect numbered headers like "2.1 Background"
        numbered_header = re.match(r'^(\d+(?:\.\d+)*)\s+(.+)$', line)
        if not lines[i-1].strip() and numbered_header:
            flush_paragraph()
            level = numbered_header.group(1).count('.') + 1  # Convert 2.1 → level 2
            header_text = numbered_header.group(2)
            # Never go beyond ### for subsections
            md_level = min(level + 1, 6)   # 1 → ##, 2 → ###, 3 → #### etc
            output.append(f'{"#" * md_level} {header_text}')
            in_header = True
            continue            


        # Detect authors
        if page_number == 1 and author_pattern.match(line):
            # Clean and format author names
            authors = re.sub(r'[†â€]', '', line)  # Remove affiliation markers
            authors = re.split(r', | and ', authors)
            formatted_authors = []
            for author in authors:
                if author.strip():
                    # Handle "First Last" formatting
                    parts = [p for p in author.strip().split() if p]
                    formatted = ' '.join(parts)
                    formatted_authors.append(f'**{formatted}**')

            # Join with commas and "and"
            if len(formatted_authors) > 1:
                joined = ', '.join(formatted_authors[:-1]) + ' and ' + formatted_authors[-1]
            else:
                joined = formatted_authors[0]

            output.append(joined)
            continue

        # Detect affiliation
        if affiliation_pattern.match(line):
            output.append(f'*{line}*')
            continue

        # Detect emails
        if email_pattern.match(line):
            output.append(f'`{line}`')
            continue

        # Detect section headers
        if re.match(r'^(Abstract|\d+\s+[A-Z]|References|Appendix|Figure|Table)', line):
            flush_paragraph()
            output.append(f'_[{line}]_')
            in_header = True
            continue


        # Handle quotes
        if quote_pattern.match(line):
            flush_paragraph()
            output.append(f'> {line}')
            continue

        # Handle hyphenated words
        if line.endswith('-'):
            current_paragraph.append(line[:-1].strip())
        else:
            current_paragraph.append(line)

        # Handle paragraph breaks after headers
        if in_header and not line.endswith(('.', '!', '?')):
            flush_paragraph()
            in_header = False

    flush_paragraph()

    # Post-processing
    markdown = '\n\n'.join(output)

    # Fix common citation patterns
    markdown = re.sub(r'\(([A-Z][a-z]+ et al\. \d{4})\)', r'[\1]', markdown)

    # Fix escaped characters
    markdown = markdown.replace('\\ud835', '').replace('\\u2020', '†')

    # Remove leftover hyphens and fix spacing
    markdown = re.sub(r'\s+-\s+', '', markdown)  # Join hyphenated words
    markdown = re.sub(r'\s+([.,!?)])', r'\1', markdown)  # Fix punctuation spacing


    return markdown