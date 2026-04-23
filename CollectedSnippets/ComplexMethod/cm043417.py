def clean_pdf_text_to_html(page_number, text):
    # Decode Unicode escapes and handle surrogate pairs
    try:
        decoded = text.encode('latin-1').decode('unicode-escape')
        decoded = decoded.encode('utf-16', 'surrogatepass').decode('utf-16')
    except Exception as e:
        decoded = text  # Fallback if decoding fails

    article_title_detected = False
    # decoded = re.sub(r'\.\n', '.\n\n', decoded)
    # decoded = re.sub(r'\.\n', '<|break|>', decoded)
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
                # escaped_para = html.escape(para)
                escaped_para = para
                # escaped_para = re.sub(r'\.\n', '.\n\n', escaped_para)
                # Split escaped_para by <|break|> to avoid HTML escaping
                escaped_para = escaped_para.split('.\n\n')
                # Wrap each part in <p> tag
                escaped_para = [f'<p>{part}</p>' for part in escaped_para]
                output.append(f'<div class="paragraph">{"".join(escaped_para)}</div><hr/>')
            current_paragraph.clear()

    for i, line in enumerate(lines):
        line = line.strip()

        # Handle empty lines
        if not line:
            flush_paragraph()
            continue

        # Detect article title (first line with reasonable length)
        if not article_title_detected and i == 0 and 3 <= len(line.split()) <= 8 and len(lines) > 1:
            flush_paragraph()
            escaped_line = html.escape(line)
            output.append(f'<h2>{escaped_line}</h2>')
            article_title_detected = True
            continue

        # Detect numbered headers like "2.1 Background"
        numbered_header = re.match(r'^(\d+(?:\.\d+)*)\s+(.+)$', line)
        if i > 0 and not lines[i-1].strip() and numbered_header:
            flush_paragraph()
            level = numbered_header.group(1).count('.') + 1
            header_text = numbered_header.group(2)
            md_level = min(level + 1, 6)
            escaped_header = html.escape(header_text)
            output.append(f'<h{md_level}>{escaped_header}</h{md_level}>')
            in_header = True
            continue

        # Detect authors
        if page_number == 1 and author_pattern.match(line):
            authors = re.sub(r'[†â€]', '', line)
            authors = re.split(r', | and ', authors)
            formatted_authors = []
            for author in authors:
                if author.strip():
                    parts = [p for p in author.strip().split() if p]
                    formatted = ' '.join(parts)
                    escaped_author = html.escape(formatted)
                    formatted_authors.append(f'<strong>{escaped_author}</strong>')

            if len(formatted_authors) > 1:
                joined = ', '.join(formatted_authors[:-1]) + ' and ' + formatted_authors[-1]
            else:
                joined = formatted_authors[0]

            output.append(f'<p>{joined}</p>')
            continue

        # Detect affiliation
        if affiliation_pattern.match(line):
            escaped_line = html.escape(line)
            output.append(f'<p><em>{escaped_line}</em></p>')
            continue

        # Detect emails
        if email_pattern.match(line):
            escaped_line = html.escape(line)
            output.append(f'<p><code>{escaped_line}</code></p>')
            continue

        # Detect section headers
        if re.match(r'^(Abstract|\d+\s+[A-Z]|References|Appendix|Figure|Table)', line):
            flush_paragraph()
            escaped_line = html.escape(line)
            output.append(f'<h2 class="section-header"><em>{escaped_line}</em></h2>')
            in_header = True
            continue

        # Handle quotes
        if quote_pattern.match(line):
            flush_paragraph()
            escaped_line = html.escape(line)
            output.append(f'<blockquote><p>{escaped_line}</p></blockquote>')
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

    # Post-process HTML
    html_output = '\n'.join(output)

    # Fix common citation patterns
    html_output = re.sub(r'\(([A-Z][a-z]+ et al\. \d{4})\)', r'<cite>\1</cite>', html_output)

    # Fix escaped characters
    html_output = html_output.replace('\\ud835', '').replace('\\u2020', '†')

    # Remove leftover hyphens and fix spacing
    html_output = re.sub(r'\s+-\s+', '', html_output)
    html_output = re.sub(r'\s+([.,!?)])', r'\1', html_output)

    return html_output