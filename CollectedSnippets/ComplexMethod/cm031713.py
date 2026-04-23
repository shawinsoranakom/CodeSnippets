def directive_output(
        self,
        command_or_name: str,
        destination: str = ''
    ) -> None:
        fd = self.clinic.destination_buffers

        if command_or_name == "preset":
            preset = self.clinic.presets.get(destination)
            if not preset:
                fail(f"Unknown preset {destination!r}!")
            fd.update(preset)
            return

        if command_or_name == "push":
            self.clinic.destination_buffers_stack.append(fd.copy())
            return

        if command_or_name == "pop":
            if not self.clinic.destination_buffers_stack:
                fail("Can't 'output pop', stack is empty!")
            previous_fd = self.clinic.destination_buffers_stack.pop()
            fd.update(previous_fd)
            return

        # secret command for debugging!
        if command_or_name == "print":
            self.block.output.append(pprint.pformat(fd))
            self.block.output.append('\n')
            return

        d = self.clinic.get_destination_buffer(destination)

        if command_or_name == "everything":
            for name in list(fd):
                fd[name] = d
            return

        if command_or_name not in fd:
            allowed = ["preset", "push", "pop", "print", "everything"]
            allowed.extend(fd)
            fail(f"Invalid command or destination name {command_or_name!r}. "
                 "Must be one of:\n -",
                 "\n - ".join([repr(word) for word in allowed]))
        fd[command_or_name] = d