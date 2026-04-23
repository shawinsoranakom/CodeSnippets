def set_message():
            with display_message_lock:
                if display_message:
                    with legacy_caching.suppress_cached_st_function_warning():
                        with caching.suppress_cached_st_function_warning():
                            spinner_proto = SpinnerProto()
                            spinner_proto.text = clean_text(text)
                            message._enqueue("spinner", spinner_proto)