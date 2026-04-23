def sort_callbacks(category, unordered_callbacks, *, enable_user_sort=True):
    callbacks = unordered_callbacks.copy()
    callback_lookup = {x.name: x for x in callbacks}
    dependencies = {}

    order_instructions = {}
    for extension in extensions.extensions:
        for order_instruction in extension.metadata.list_callback_order_instructions():
            if order_instruction.name in callback_lookup:
                if order_instruction.name not in order_instructions:
                    order_instructions[order_instruction.name] = []

                order_instructions[order_instruction.name].append(order_instruction)

    if order_instructions:
        for callback in callbacks:
            dependencies[callback.name] = []

        for callback in callbacks:
            for order_instruction in order_instructions.get(callback.name, []):
                for after in order_instruction.after:
                    if after not in callback_lookup:
                        continue

                    dependencies[callback.name].append(after)

                for before in order_instruction.before:
                    if before not in callback_lookup:
                        continue

                    dependencies[before].append(callback.name)

        sorted_names = util.topological_sort(dependencies)
        callbacks = [callback_lookup[x] for x in sorted_names]

    if enable_user_sort:
        for name in reversed(getattr(shared.opts, 'prioritized_callbacks_' + category, [])):
            index = next((i for i, callback in enumerate(callbacks) if callback.name == name), None)
            if index is not None:
                callbacks.insert(0, callbacks.pop(index))

    return callbacks