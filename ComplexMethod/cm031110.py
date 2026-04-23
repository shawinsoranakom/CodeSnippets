def decode(self, input, final=False):
        output = ''
        for b in input:
            if self.i == 0: # variable-length, terminated with period
                if b == ord('.'):
                    if self.buffer:
                        output += self.process_word()
                else:
                    self.buffer.append(b)
            else: # fixed-length, terminate after self.i bytes
                self.buffer.append(b)
                if len(self.buffer) == self.i:
                    output += self.process_word()
        if final and self.buffer: # EOF terminates the last word
            output += self.process_word()
        return output