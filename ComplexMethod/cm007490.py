def is_rented():
            if '>You rented this title.<' in webpage:
                return True
            if try_get(config, lambda x: x['user']['purchased']):
                return True
            for purchase_option in (vod.get('purchase_options') or []):
                if purchase_option.get('purchased'):
                    return True
                label = purchase_option.get('label_string')
                if label and (label.startswith('You rented this') or label.endswith(' remaining')):
                    return True
            return False