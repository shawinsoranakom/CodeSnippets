def render(self, context):
        if "forloop" in context:
            parentloop = context["forloop"]
        else:
            parentloop = {}
        with context.push():
            values = self.sequence.resolve(context, ignore_failures=True)
            if values is None:
                values = []
            if not hasattr(values, "__len__"):
                values = list(values)
            len_values = len(values)
            if len_values < 1:
                return self.nodelist_empty.render(context)
            nodelist = []
            if self.is_reversed:
                values = reversed(values)
            num_loopvars = len(self.loopvars)
            unpack = num_loopvars > 1
            # Create a forloop value in the context. We'll update counters on
            # each iteration just below.
            loop_dict = context["forloop"] = {
                "parentloop": parentloop,
                "length": len_values,
            }
            for i, item in enumerate(values):
                # Shortcuts for current loop iteration number.
                loop_dict["counter0"] = i
                loop_dict["counter"] = i + 1
                # Reverse counter iteration numbers.
                loop_dict["revcounter"] = len_values - i
                loop_dict["revcounter0"] = len_values - i - 1
                # Boolean values designating first and last times through loop.
                loop_dict["first"] = i == 0
                loop_dict["last"] = i == len_values - 1

                pop_context = False
                if unpack:
                    # If there are multiple loop variables, unpack the item
                    # into them.
                    try:
                        len_item = len(item)
                    except TypeError:  # not an iterable
                        len_item = 1
                    # Check loop variable count before unpacking
                    if num_loopvars != len_item:
                        raise ValueError(
                            "Need {} values to unpack in for loop; got {}. ".format(
                                num_loopvars, len_item
                            ),
                        )
                    unpacked_vars = dict(zip(self.loopvars, item))
                    pop_context = True
                    context.update(unpacked_vars)
                else:
                    context[self.loopvars[0]] = item

                for node in self.nodelist_loop:
                    nodelist.append(node.render_annotated(context))

                if pop_context:
                    # Pop the loop variables pushed on to the context to avoid
                    # the context ending up in an inconsistent state when other
                    # tags (e.g., include and with) push data to context.
                    context.pop()
        return mark_safe("".join(nodelist))