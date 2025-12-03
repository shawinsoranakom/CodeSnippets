def load_config(path):
    default = {
        'ltr_keywords': [],
        'ltr_symbols': [],
        'pure_ltr_pattern': r"^[\u0000-\u007F]+$",
        'rtl_chars_pattern': r"[\u0590-\u08FF]",
        'severity': {
            'bidi_mismatch': 'error', 
            'keyword': 'warning',    
            'symbol': 'warning',       
            'pure_ltr': 'notice',       
            'author_meta': 'notice'   
        },
        'ignore_meta': ['PDF', 'EPUB', 'HTML', 'podcast', 'videocast'],
        'min_ltr_length': 3,
        'rlm_entities': ['&rlm;', '&#x200F;', '&#8207;'],
        'lrm_entities': ['&lrm;', '&#x200E;', '&#8206;']
    }

   
    if path and os.path.exists(path):
        try:
            with open(path, encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
                conf = data.get('rtl_config', {})
                default.update(conf)
        except Exception as e:
            print(f"::warning file={path}::Could not load config: {e}. Using defaults.")


    return default
