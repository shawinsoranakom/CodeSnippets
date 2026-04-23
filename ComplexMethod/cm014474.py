def grab_method_and_template(in_kernel):
        # The positions for relevant kernel components.
        pos = {
            "kernel_launch": {"start": in_kernel["start"], "end": in_kernel["end"]},
            "kernel_name": {"start": -1, "end": -1},
            "template": {"start": -1, "end": -1}
        }

        # Count for balancing template
        count = {"<>": 0}

        # Status for whether we are parsing a certain item.
        START = 0
        AT_TEMPLATE = 1
        AFTER_TEMPLATE = 2
        AT_KERNEL_NAME = 3

        status = START

        # Parse the string character by character
        for i in range(pos["kernel_launch"]["start"] - 1, -1, -1):
            char = string[i]

            # Handle Templating Arguments
            if status in (START, AT_TEMPLATE):
                if char == ">":
                    if status == START:
                        status = AT_TEMPLATE
                        pos["template"]["end"] = i
                    count["<>"] += 1

                if char == "<":
                    count["<>"] -= 1
                    if count["<>"] == 0 and (status == AT_TEMPLATE):
                        pos["template"]["start"] = i
                        status = AFTER_TEMPLATE

            # Handle Kernel Name
            if status != AT_TEMPLATE:
                if string[i].isalnum() or string[i] in {'(', ')', '_', ':', '#'}:
                    if status != AT_KERNEL_NAME:
                        status = AT_KERNEL_NAME
                        pos["kernel_name"]["end"] = i

                    # Case: Kernel name starts the string.
                    if i == 0:
                        pos["kernel_name"]["start"] = 0

                        # Finished
                        return [(pos["kernel_name"]), (pos["template"]), (pos["kernel_launch"])]

                else:
                    # Potential ending point if we're already traversing a kernel's name.
                    if status == AT_KERNEL_NAME:
                        pos["kernel_name"]["start"] = i

                        # Finished
                        return [(pos["kernel_name"]), (pos["template"]), (pos["kernel_launch"])]