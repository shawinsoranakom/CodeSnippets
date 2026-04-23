def _line_iterator():
        """Yields from/to lines of text with a change indication.

        This function is an iterator.  It itself pulls lines from a
        differencing iterator, processes them and yields them.  When it can
        it yields both a "from" and a "to" line, otherwise it will yield one
        or the other.  In addition to yielding the lines of from/to text, a
        boolean flag is yielded to indicate if the text line(s) have
        differences in them.

        Note, this function is purposefully not defined at the module scope so
        that data it needs from its parent function (within whose context it
        is defined) does not need to be of module scope.
        """
        lines = []
        num_blanks_pending, num_blanks_to_yield = 0, 0
        while True:
            # Load up next 4 lines so we can look ahead, create strings which
            # are a concatenation of the first character of each of the 4 lines
            # so we can do some very readable comparisons.
            while len(lines) < 4:
                lines.append(next(diff_lines_iterator, 'X'))
            s = ''.join([line[0] for line in lines])
            if s.startswith('X'):
                # When no more lines, pump out any remaining blank lines so the
                # corresponding add/delete lines get a matching blank line so
                # all line pairs get yielded at the next level.
                num_blanks_to_yield = num_blanks_pending
            elif s.startswith('-?+?'):
                # simple intraline change
                yield _make_line(lines,'?',0), _make_line(lines,'?',1), True
                continue
            elif s.startswith('--++'):
                # in delete block, add block coming: we do NOT want to get
                # caught up on blank lines yet, just process the delete line
                num_blanks_pending -= 1
                yield _make_line(lines,'-',0), None, True
                continue
            elif s.startswith(('--?+', '--+', '- ')):
                # in delete block and see an intraline change or unchanged line
                # coming: yield the delete line and then blanks
                from_line,to_line = _make_line(lines,'-',0), None
                num_blanks_to_yield,num_blanks_pending = num_blanks_pending-1,0
            elif s.startswith('-+?'):
                # intraline change
                yield _make_line(lines,None,0), _make_line(lines,'?',1), True
                continue
            elif s.startswith('-?+'):
                # intraline change
                yield _make_line(lines,'?',0), _make_line(lines,None,1), True
                continue
            elif s.startswith('-'):
                # delete FROM line
                num_blanks_pending -= 1
                yield _make_line(lines,'-',0), None, True
                continue
            elif s.startswith('+--'):
                # in add block, delete block coming: we do NOT want to get
                # caught up on blank lines yet, just process the add line
                num_blanks_pending += 1
                yield None, _make_line(lines,'+',1), True
                continue
            elif s.startswith(('+ ', '+-')):
                # will be leaving an add block: yield blanks then add line
                from_line, to_line = None, _make_line(lines,'+',1)
                num_blanks_to_yield,num_blanks_pending = num_blanks_pending+1,0
            elif s.startswith('+'):
                # inside an add block, yield the add line
                num_blanks_pending += 1
                yield None, _make_line(lines,'+',1), True
                continue
            elif s.startswith(' '):
                # unchanged text, yield it to both sides
                yield _make_line(lines[:],None,0),_make_line(lines,None,1),False
                continue
            # Catch up on the blank lines so when we yield the next from/to
            # pair, they are lined up.
            while(num_blanks_to_yield < 0):
                num_blanks_to_yield += 1
                yield None,('','\n'),True
            while(num_blanks_to_yield > 0):
                num_blanks_to_yield -= 1
                yield ('','\n'),None,True
            if s.startswith('X'):
                return
            else:
                yield from_line,to_line,True