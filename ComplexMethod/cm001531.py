def remove_current_script_callbacks():
    stack = [x for x in inspect.stack() if x.filename != __file__]
    filename = stack[0].filename if stack else 'unknown file'
    if filename == 'unknown file':
        return
    for callback_list in callback_map.values():
        for callback_to_remove in [cb for cb in callback_list if cb.script == filename]:
            callback_list.remove(callback_to_remove)
    for ordered_callbacks_list in ordered_callbacks_map.values():
        for callback_to_remove in [cb for cb in ordered_callbacks_list if cb.script == filename]:
            ordered_callbacks_list.remove(callback_to_remove)