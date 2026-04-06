def match(command):
    return (u'install' in command.script_parts
            and u'brew cask install' in command.output)