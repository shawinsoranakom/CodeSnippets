def read_process_output(self, proc, num_lines_to_read):
        num_lines_read = 0
        output = ""

        while num_lines_read < num_lines_to_read:
            output += proc.stdout.readline().decode("UTF-8")
            num_lines_read += 1

        return output