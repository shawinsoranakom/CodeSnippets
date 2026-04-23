def _iter_use_action_sets(self, interp1, interp2):
        interps = (interp1, interp2)

        # only recv end used
        yield [
            ChannelAction('use', 'recv', interp1),
            ]
        yield [
            ChannelAction('use', 'recv', interp2),
            ]
        yield [
            ChannelAction('use', 'recv', interp1),
            ChannelAction('use', 'recv', interp2),
            ]

        # never emptied
        yield [
            ChannelAction('use', 'send', interp1),
            ]
        yield [
            ChannelAction('use', 'send', interp2),
            ]
        yield [
            ChannelAction('use', 'send', interp1),
            ChannelAction('use', 'send', interp2),
            ]

        # partially emptied
        for interp1 in interps:
            for interp2 in interps:
                for interp3 in interps:
                    yield [
                        ChannelAction('use', 'send', interp1),
                        ChannelAction('use', 'send', interp2),
                        ChannelAction('use', 'recv', interp3),
                        ]

        # fully emptied
        for interp1 in interps:
            for interp2 in interps:
                for interp3 in interps:
                    for interp4 in interps:
                        yield [
                            ChannelAction('use', 'send', interp1),
                            ChannelAction('use', 'send', interp2),
                            ChannelAction('use', 'recv', interp3),
                            ChannelAction('use', 'recv', interp4),
                            ]