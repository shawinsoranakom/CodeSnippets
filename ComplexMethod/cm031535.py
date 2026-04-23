def delete(self, index1, index2=None):
        '''Delete slice from index1 to index2 (default is 'index1+1').

        Adjust default index2 ('index+1) for line ends.
        Do not delete the terminal \n at the very end of self.data ([-1][-1]).
        '''
        startline, startchar = self._decode(index1, -1)
        if index2 is None:
            if startchar < len(self.data[startline])-1:
                # not deleting \n
                endline, endchar = startline, startchar+1
            elif startline < len(self.data) - 1:
                # deleting non-terminal \n, convert 'index1+1 to start of next line
                endline, endchar = startline+1, 0
            else:
                # do not delete terminal \n if index1 == 'insert'
                return
        else:
            endline, endchar = self._decode(index2, -1)
            # restricting end position to insert position excludes terminal \n

        if startline == endline and startchar < endchar:
            self.data[startline] = self.data[startline][:startchar] + \
                                             self.data[startline][endchar:]
        elif startline < endline:
            self.data[startline] = self.data[startline][:startchar] + \
                                   self.data[endline][endchar:]
            startline += 1
            for i in range(startline, endline+1):
                del self.data[startline]