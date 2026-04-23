def help(self, request, is_cli=False):
        if isinstance(request, str):
            request = request.strip()
            if request == 'keywords': self.listkeywords()
            elif request == 'symbols': self.listsymbols()
            elif request == 'topics': self.listtopics()
            elif request == 'modules': self.listmodules()
            elif request[:8] == 'modules ':
                self.listmodules(request.split()[1])
            elif request in self.symbols: self.showsymbol(request)
            elif request in ['True', 'False', 'None']:
                # special case these keywords since they are objects too
                doc(eval(request), 'Help on %s:', output=self._output, is_cli=is_cli)
            elif request in self.keywords: self.showtopic(request)
            elif request in self.topics: self.showtopic(request)
            elif request: doc(request, 'Help on %s:', output=self._output, is_cli=is_cli)
            else: doc(str, 'Help on %s:', output=self._output, is_cli=is_cli)
        elif isinstance(request, Helper): self()
        else: doc(request, 'Help on %s:', output=self._output, is_cli=is_cli)
        self.output.write('\n')