def match(command):
    return (' is not a tsuru command. See "tsuru help".' in command.output
            and '\nDid you mean?\n\t' in command.output)