def dump(self, file, trace=0):
        # write data to file, as a C array
        size = getsize(self.data)
        if trace:
            print(self.name+":", size*len(self.data), "bytes", file=sys.stderr)
        file.write("static const ")
        if size == 1:
            file.write("unsigned char")
        elif size == 2:
            file.write("unsigned short")
        else:
            file.write("unsigned int")
        file.write(" " + self.name + "[] = {\n")
        if self.data:
            s = "    "
            for item in self.data:
                i = str(item) + ", "
                if len(s) + len(i) > 78:
                    file.write(s.rstrip() + "\n")
                    s = "    " + i
                else:
                    s = s + i
            if s.strip():
                file.write(s.rstrip() + "\n")
        file.write("};\n\n")