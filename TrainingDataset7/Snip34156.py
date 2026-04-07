def echo(parser, token):
    return EchoNode(token.contents.split()[1:])