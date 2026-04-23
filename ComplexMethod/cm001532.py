def remove_callbacks_for_function(callback_func):
    for callback_list in callback_map.values():
        for callback_to_remove in [cb for cb in callback_list if cb.callback == callback_func]:
            callback_list.remove(callback_to_remove)
    for ordered_callback_list in ordered_callbacks_map.values():
        for callback_to_remove in [cb for cb in ordered_callback_list if cb.callback == callback_func]:
            ordered_callback_list.remove(callback_to_remove)