def upgrade(file_manager: FileManager):
    upgrade_domain = UpgradeDomainTransformer()
    no_whitespace = functools.partial(re.compile(r'\s', re.MULTILINE).sub, '')
    for file in file_manager:
        if not (file.path.parent.name in ('data', 'report', 'views') and file.path.suffix == '.xml'):
            continue
        content = file.content
        # tree = etree.fromstring(content)  # does not support declarations
        try:
            tree = etree.parse(io.BytesIO(bytes(content, 'utf-8')))
        except Exception as e:  # noqa: BLE001
            _logger.info("Failed to parse the file %s: %s", file.path, e)
            continue
        replacements = {}
        all_domains = [el.attrib['domain'] for el in tree.findall('.//filter[@domain]')]
        all_domains.extend(el.text for el in tree.findall(".//field[@name='domain_force']"))
        all_domains.extend(el.text for el in tree.findall(".//field[@name='domain']"))
        for domain in all_domains:
            if not domain:
                continue
            try:
                new_domain = upgrade_domain.transform(domain)
                replacements[no_whitespace(domain)] = new_domain
            except NoChange as e:
                _logger.debug("No change %s", e)
            except Exception:  # noqa: BLE001
                # check if contains dynamic part
                level = logging.INFO if re.search(r"%\([a-z0-9\.]+\)[sd]", domain) else logging.WARNING
                _logger.log(level, "Failed to parse the domain %r", domain)
        if not replacements:
            continue

        def replacement_attr(match):
            value = etree.fromstring(f"<x {match[0]} />").attrib["domain"]
            domain = replacements.get(no_whitespace(value))
            if not domain:
                return match[0]
            domain = domain.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            raw_value = repr(domain).strip('"')
            return f"{match[1]}{raw_value}{match[3]}"

        def replacement_tag(match):
            value = etree.fromstring(f"<x>{match[2]}</x>").text
            domain = replacements.get(no_whitespace(value))
            if not domain:
                return match[0]
            domain = domain.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            return f"{match[1]}{domain}{match[3]}"

        content = re.sub(r'(domain=")(.+?)(")', replacement_attr, content, flags=re.MULTILINE | re.DOTALL)
        content = re.sub(r'(name="(?:domain|domain_force)"[^>]*>)(.+?)(<)', replacement_tag, content, flags=re.MULTILINE | re.DOTALL)
        file.content = content