def format_document_soup(
    document: bs4.BeautifulSoup, table_cell_separator: str = "\t"
) -> str:
    """Format html to a flat text document.

    The following goals:
    - Newlines from within the HTML are removed (as browser would ignore them as well).
    - Repeated newlines/spaces are removed (as browsers would ignore them).
    - Newlines only before and after headlines and paragraphs or when explicit (br or pre tag)
    - Table columns/rows are separated by newline
    - List elements are separated by newline and start with a hyphen
    """
    text = ""
    list_element_start = False
    verbatim_output = 0
    in_table = False
    last_added_newline = False
    link_href: str | None = None

    for e in document.descendants:
        verbatim_output -= 1
        if isinstance(e, bs4.element.NavigableString):
            if isinstance(e, (bs4.element.Comment, bs4.element.Doctype)):
                continue
            element_text = e.text
            if in_table:
                # Tables are represented in natural language with rows separated by newlines
                # Can't have newlines then in the table elements
                element_text = element_text.replace("\n", " ").strip()

            # Some tags are translated to spaces but in the logic underneath this section, we
            # translate them to newlines as a browser should render them such as with br
            # This logic here avoids a space after newline when it shouldn't be there.
            if last_added_newline and element_text.startswith(" "):
                element_text = element_text[1:]
                last_added_newline = False

            if element_text:
                content_to_add = (
                    element_text
                    if verbatim_output > 0
                    else format_element_text(element_text, link_href)
                )

                # Don't join separate elements without any spacing
                if (text and not text[-1].isspace()) and (
                    content_to_add and not content_to_add[0].isspace()
                ):
                    text += " "

                text += content_to_add

                list_element_start = False
        elif isinstance(e, bs4.element.Tag):
            # table is standard HTML element
            if e.name == "table":
                in_table = True
            # TR is for rows
            elif e.name == "tr" and in_table:
                text += "\n"
            # td for data cell, th for header
            elif e.name in ["td", "th"] and in_table:
                text += table_cell_separator
            elif e.name == "/table":
                in_table = False
            elif in_table:
                # don't handle other cases while in table
                pass
            elif e.name == "a":
                href_value = e.get("href", None)
                # mostly for typing, having multiple hrefs is not valid HTML
                link_href = (
                    href_value[0] if isinstance(href_value, list) else href_value
                )
            elif e.name == "/a":
                link_href = None
            elif e.name in ["p", "div"]:
                if not list_element_start:
                    text += "\n"
            elif e.name in ["h1", "h2", "h3", "h4"]:
                text += "\n"
                list_element_start = False
                last_added_newline = True
            elif e.name == "br":
                text += "\n"
                list_element_start = False
                last_added_newline = True
            elif e.name == "li":
                text += "\n- "
                list_element_start = True
            elif e.name == "pre":
                if verbatim_output <= 0:
                    verbatim_output = len(list(e.childGenerator()))
    return strip_excessive_newlines_and_spaces(text)