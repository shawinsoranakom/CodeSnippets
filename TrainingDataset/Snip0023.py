def find_links_in_file(filename: str) -> List[str]:
    """Find links in a file and return a list of URLs from text file."""

    with open(filename, mode='r', encoding='utf-8') as file:
        readme = file.read()
        index_section = readme.find('## Index')
        if index_section == -1:
            index_section = 0
        content = readme[index_section:]

    links = find_links_in_text(content)

    return links
