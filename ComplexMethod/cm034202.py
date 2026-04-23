def _tty_ify_sem_complex(matcher):
        text = DocCLI._UNESCAPE.sub(r'\1', matcher.group(1))
        value = None
        if '=' in text:
            text, value = text.split('=', 1)
        m = DocCLI._FQCN_TYPE_PREFIX_RE.match(text)
        if m:
            plugin_fqcn = m.group(1)
            plugin_type = m.group(2)
            text = m.group(3)
        elif text.startswith(DocCLI._IGNORE_MARKER):
            text = text[len(DocCLI._IGNORE_MARKER):]
            plugin_fqcn = plugin_type = ''
        else:
            plugin_fqcn = plugin_type = ''
        entrypoint = None
        if ':' in text:
            entrypoint, text = text.split(':', 1)
        if value is not None:
            text = f"{text}={value}"
        if plugin_fqcn and plugin_type:
            plugin_suffix = '' if plugin_type in ('role', 'module', 'playbook') else ' plugin'
            plugin = f"{plugin_type}{plugin_suffix} {plugin_fqcn}"
            if plugin_type == 'role' and entrypoint is not None:
                plugin = f"{plugin}, {entrypoint} entrypoint"
            return f"`{text}' (of {plugin})"
        return f"`{text}'"