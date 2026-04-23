def parseNotebook(filename, enable_markdown=1):
    import json

    CodeBlocks = []
    with open(filename, 'r', encoding='utf-8', errors='replace') as f:
        notebook = json.load(f)
    for cell in notebook['cells']:
        if cell['cell_type'] == 'code' and cell['source']:
            # remove blank lines
            cell['source'] = [line for line in cell['source'] if line.strip()
                              != '']
            CodeBlocks.append("".join(cell['source']))
        elif enable_markdown and cell['cell_type'] == 'markdown' and cell['source']:
            cell['source'] = [line for line in cell['source'] if line.strip()
                              != '']
            CodeBlocks.append("Markdown:"+"".join(cell['source']))

    Code = ""
    for idx, code in enumerate(CodeBlocks):
        Code += f"This is {idx+1}th code block: \n"
        Code += code+"\n"

    return Code