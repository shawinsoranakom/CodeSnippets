def fix_chat_template(tokenizer):
    chat_template = getattr(tokenizer, "chat_template", None)
    if chat_template is None:
        return None

    # Multi-variant dict (e.g. Hermes-3 {default, tool_use}): route each
    # variant through the full repair contract via _VariantTokenizerProxy.
    if isinstance(chat_template, dict):
        fixed = {}
        for key, tmpl in chat_template.items():
            if not isinstance(tmpl, str):
                fixed[key] = tmpl
                continue
            proxy = _VariantTokenizerProxy(
                tokenizer, tmpl, variant_label = f"variant={key!r}"
            )
            fixed[key] = _fix_chat_template_for_tokenizer(proxy, tmpl)
        return fixed

    # List-of-dicts form (older HF multi-template style).
    if isinstance(chat_template, list):
        fixed = []
        for item in chat_template:
            if not isinstance(item, dict) or "template" not in item:
                fixed.append(item)
                continue
            tmpl = item["template"]
            if not isinstance(tmpl, str):
                fixed.append(item)
                continue
            label = f"variant={item.get('name', '?')!r}"
            proxy = _VariantTokenizerProxy(tokenizer, tmpl, variant_label = label)
            new_tmpl = _fix_chat_template_for_tokenizer(proxy, tmpl)
            if new_tmpl is tmpl or new_tmpl == tmpl:
                fixed.append(item)
            else:
                fixed.append({**item, "template": new_tmpl})
        return fixed

    return _fix_chat_template_for_tokenizer(tokenizer, chat_template)