def getaddress(self):
        """Parse the next address."""
        self.commentlist = []
        self.gotonext()

        oldpos = self.pos
        oldcl = self.commentlist
        plist = self.getphraselist()

        self.gotonext()
        returnlist = []

        if self.pos >= len(self.field):
            # Bad email address technically, no domain.
            if plist:
                returnlist = [(SPACE.join(self.commentlist), plist[0])]

        elif self.field[self.pos] in '.@':
            # email address is just an addrspec
            # this isn't very efficient since we start over
            self.pos = oldpos
            self.commentlist = oldcl
            addrspec = self.getaddrspec()
            returnlist = [(SPACE.join(self.commentlist), addrspec)]

        elif self.field[self.pos] == ':':
            # address is a group
            returnlist = []

            fieldlen = len(self.field)
            self.pos += 1
            while self.pos < len(self.field):
                self.gotonext()
                if self.pos < fieldlen and self.field[self.pos] == ';':
                    self.pos += 1
                    break
                returnlist = returnlist + self.getaddress()

        elif self.field[self.pos] == '<':
            # Address is a phrase then a route addr
            routeaddr = self.getrouteaddr()

            if self.commentlist:
                returnlist = [(SPACE.join(plist) + ' (' +
                               ' '.join(self.commentlist) + ')', routeaddr)]
            else:
                returnlist = [(SPACE.join(plist), routeaddr)]

        else:
            if plist:
                returnlist = [(SPACE.join(self.commentlist), plist[0])]
            elif self.field[self.pos] in self.specials:
                self.pos += 1

        self.gotonext()
        if self.pos < len(self.field) and self.field[self.pos] == ',':
            self.pos += 1
        return returnlist