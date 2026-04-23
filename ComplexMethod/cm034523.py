def _log(self, msg: str, color: str | None = None, caplevel: int | None = None):

        if logger and (caplevel is None or self.log_verbosity > caplevel):
            msg2 = msg.lstrip('\n')

            if caplevel is None or caplevel > 0:
                lvl = logging.INFO
            elif caplevel == -1:
                lvl = logging.ERROR
            elif caplevel == -2:
                lvl = logging.WARNING
            elif caplevel == -3:
                lvl = logging.DEBUG
            elif color:
                # set logger level based on color (not great)
                # but last resort and backwards compatible
                try:
                    lvl = color_to_log_level[color]
                except KeyError:
                    # this should not happen if mapping is updated with new color configs, but JIC
                    raise AnsibleAssertionError('Invalid color supplied to display: %s' % color)

            # actually log
            logger.log(lvl, msg2)