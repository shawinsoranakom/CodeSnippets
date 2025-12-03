def get_categories_content(contents: List[str]) -> Tuple[Categories, CategoriesLineNumber]:

    categories = {}
    category_line_num = {}

    for line_num, line_content in enumerate(contents):

        if line_content.startswith(anchor):
            category = line_content.split(anchor)[1].strip()
            categories[category] = []
            category_line_num[category] = line_num
            continue

        if not line_content.startswith('|') or line_content.startswith('|---'):
            continue

        raw_title = [
            raw_content.strip() for raw_content in line_content.split('|')[1:-1]
        ][0]

        title_match = link_re.match(raw_title)
        if title_match:
                title = title_match.group(1).upper()
                categories[category].append(title)

    return (categories, category_line_num)
