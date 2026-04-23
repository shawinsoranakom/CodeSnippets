def _inherit_parent_code_render_metadata(block, parent_block):
    # pipeline_magic_model 会把 code_body 的 sub_type/guess_lang 提升到父 code block。
    # markdown 渲染 code_body 时需要把这两个字段临时透传回来，但不能修改原始输入。
    if block.get('type') != BlockType.CODE_BODY:
        return block
    if parent_block.get('type') != BlockType.CODE:
        return block

    needs_sub_type = 'sub_type' not in block and 'sub_type' in parent_block
    needs_guess_lang = 'guess_lang' not in block and 'guess_lang' in parent_block
    if not needs_sub_type and not needs_guess_lang:
        return block

    render_block = dict(block)
    if needs_sub_type:
        render_block['sub_type'] = parent_block['sub_type']
    if needs_guess_lang:
        render_block['guess_lang'] = parent_block['guess_lang']
    return render_block