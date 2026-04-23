def find_stores_in_tokens(tokens: list[lexer.Token], callback: Callable[[lexer.Token], None]) -> None:
        while tokens and tokens[0].kind == "COMMENT":
            tokens = tokens[1:]
        if len(tokens) < 4:
            return
        if tokens[1].kind == "EQUALS":
            if tokens[0].kind == "IDENTIFIER":
                name = tokens[0].text
                if name in outnames or name in innames:
                    callback(tokens[0])
        #Passing the address of a local is also a definition
        for idx, tkn in enumerate(tokens):
            if tkn.kind == "AND":
                name_tkn = tokens[idx+1]
                if name_tkn.text in outnames:
                    callback(name_tkn)