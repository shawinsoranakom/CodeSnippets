def mock_compile(script):
    """Simple mock compiler for demo when C4A is not available"""
    lines = [line for line in script.split('\n') if line.strip() and not line.strip().startswith('#')]
    js_code = []

    for i, line in enumerate(lines):
        line = line.strip()

        try:
            if line.startswith('GO '):
                url = line[3:].strip()
                # Handle relative URLs
                if not url.startswith(('http://', 'https://')):
                    url = '/' + url.lstrip('/')
                js_code.append(f"await page.goto('{url}');")

            elif line.startswith('WAIT '):
                parts = line[5:].strip().split(' ')
                if parts[0].startswith('`'):
                    selector = parts[0].strip('`')
                    timeout = parts[1] if len(parts) > 1 else '5'
                    js_code.append(f"await page.waitForSelector('{selector}', {{ timeout: {timeout}000 }});")
                else:
                    seconds = parts[0]
                    js_code.append(f"await page.waitForTimeout({seconds}000);")

            elif line.startswith('CLICK '):
                selector = line[6:].strip().strip('`')
                js_code.append(f"await page.click('{selector}');")

            elif line.startswith('TYPE '):
                text = line[5:].strip().strip('"')
                js_code.append(f"await page.keyboard.type('{text}');")

            elif line.startswith('SCROLL '):
                parts = line[7:].strip().split(' ')
                direction = parts[0]
                amount = parts[1] if len(parts) > 1 else '500'
                if direction == 'DOWN':
                    js_code.append(f"await page.evaluate(() => window.scrollBy(0, {amount}));")
                elif direction == 'UP':
                    js_code.append(f"await page.evaluate(() => window.scrollBy(0, -{amount}));")

            elif line.startswith('IF '):
                if 'THEN' not in line:
                    return {
                        'success': False,
                        'error': {
                            'line': i + 1,
                            'column': len(line),
                            'message': "Missing 'THEN' keyword after IF condition",
                            'suggestion': "Add 'THEN' after the condition",
                            'sourceLine': line
                        }
                    }

                condition = line[3:line.index('THEN')].strip()
                action = line[line.index('THEN') + 4:].strip()

                if 'EXISTS' in condition:
                    selector_match = condition.split('`')
                    if len(selector_match) >= 2:
                        selector = selector_match[1]
                        action_selector = action.split('`')[1] if '`' in action else ''
                        js_code.append(
                            f"if (await page.$$('{selector}').length > 0) {{ "
                            f"await page.click('{action_selector}'); }}"
                        )

            elif line.startswith('PRESS '):
                key = line[6:].strip()
                js_code.append(f"await page.keyboard.press('{key}');")

            else:
                # Unknown command
                return {
                    'success': False,
                    'error': {
                        'line': i + 1,
                        'column': 1,
                        'message': f"Unknown command: {line.split()[0]}",
                        'suggestion': "Check command syntax",
                        'sourceLine': line
                    }
                }

        except Exception as e:
            return {
                'success': False,
                'error': {
                    'line': i + 1,
                    'column': 1,
                    'message': f"Failed to parse: {str(e)}",
                    'suggestion': "Check syntax",
                    'sourceLine': line
                }
            }

    return {
        'success': True,
        'jsCode': js_code,
        'metadata': {
            'lineCount': len(js_code),
            'sourceLines': len(lines)
        }
    }