def _update_field_state_for_paragraph(para_element, field_state):
    """Update field_state by scanning a paragraph element's runs.

    Used for early-exit paragraphs (TOC / math / empty / code) to keep
    cross-paragraph field tracking accurate without building item lists.
    """
    for child in para_element:
        tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
        if tag != "r":
            continue
        fld_char = child.find(_W + "fldChar")
        if fld_char is not None:
            fld_type = fld_char.get(_W + "fldCharType")
            if fld_type == "begin":
                if field_state.phase == "result":
                    field_state.nest_depth += 1
                else:
                    field_state.active = True
                    field_state.phase = "instr"
                    field_state.url = None
            elif fld_type == "separate":
                if field_state.nest_depth == 0:
                    field_state.phase = "result"
            elif fld_type == "end":
                if field_state.nest_depth > 0:
                    field_state.nest_depth -= 1
                else:
                    field_state.active = False
                    field_state.phase = None
                    field_state.url = None
            continue
        instr_elem = child.find(_W + "instrText")
        if instr_elem is not None and field_state.phase == "instr":
            if instr_elem.text:
                m = _RE_FIELD_HYPERLINK.search(instr_elem.text)
                if m:
                    field_state.url = m.group(1)