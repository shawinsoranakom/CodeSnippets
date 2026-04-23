def _iter_close_action_sets(self, interp1, interp2):
        ends = ('recv', 'send')
        interps = (interp1, interp2)
        for force in (True, False):
            op = 'force-close' if force else 'close'
            for interp in interps:
                for end in ends:
                    yield [
                        ChannelAction(op, end, interp),
                        ]
        for recvop in ('close', 'force-close'):
            for sendop in ('close', 'force-close'):
                for recv in interps:
                    for send in interps:
                        yield [
                            ChannelAction(recvop, 'recv', recv),
                            ChannelAction(sendop, 'send', send),
                            ]