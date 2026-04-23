def markdown_to_dict(article_content):
    import markdown
    from bs4 import BeautifulSoup
    cur_t = ""
    cur_c = ""
    results = {}
    for line in article_content:
        if line.startswith('#'):
            if cur_t!="":
                if cur_t not in results:
                    results.update({cur_t:cur_c.lstrip('\n')})
                else:
                    # 处理重名的章节
                    results.update({cur_t + " " + gen_time_str():cur_c.lstrip('\n')})
            cur_t = line.rstrip('\n')
            cur_c = ""
        else:
            cur_c += line
    results_final = {}
    for k in list(results.keys()):
        if k.startswith('# '):
            results_final['title'] = k.split('# ')[-1]
            results_final['authors'] = results.pop(k).lstrip('\n')
        if k.startswith('###### Abstract'):
            results_final['abstract'] = results.pop(k).lstrip('\n')

    results_final_sections = []
    for k,v in results.items():
        results_final_sections.append({
            'heading':k.lstrip("# "),
            'text':v if len(v) > 0 else f"The beginning of {k.lstrip('# ')} section."
        })
    results_final['sections'] = results_final_sections
    return results_final