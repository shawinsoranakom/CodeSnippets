def remove_toc_pdf(items, outlines):
    if not outlines:
        return items

    toc_start_page = None
    content_start_page = None
    for i, (title, level, page_no) in enumerate(outlines):
        if re.match(r"(contents|目录|目次|table of contents|致谢|acknowledge)$", title.split("@@")[0].strip().lower()):
            toc_start_page = page_no
            for next_title, next_level, next_page_no in outlines[i + 1:]:
                if next_level != level:
                    continue
                if re.match(r"(contents|目录|目次|table of contents|致谢|acknowledge)$", next_title.split("@@")[0].strip().lower()):
                    continue
                content_start_page = next_page_no
                break
            break

    if content_start_page:
        return [item for item in items if not (toc_start_page <= item["page_number"] < content_start_page)]
    return items