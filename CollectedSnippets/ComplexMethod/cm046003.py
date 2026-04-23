def get_data_from_spans(lines):
        for line in lines:
            for span in line.get('spans', []):
                span_type = span.get('type')
                if span_type == ContentType.TABLE:
                    return span.get('image_path', ''), span.get('html', '')
                elif span_type == ContentType.CHART:
                    return span.get('image_path', ''), span.get('content', '')
                elif span_type == ContentType.IMAGE:
                    return span.get('image_path', ''), span.get('content', '')
                elif span_type == ContentType.INTERLINE_EQUATION:
                    return span.get('image_path', ''), span.get('content', '')
                elif span_type == ContentType.TEXT:
                    return '', span.get('content', '')
        return '', ''