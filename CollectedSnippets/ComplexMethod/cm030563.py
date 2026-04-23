def testAttributes(self):
        # test that exception attributes are happy

        exceptionList = [
            (BaseException, (), {}, {'args' : ()}),
            (BaseException, (1, ), {}, {'args' : (1,)}),
            (BaseException, ('foo',), {},
                {'args' : ('foo',)}),
            (BaseException, ('foo', 1), {},
                {'args' : ('foo', 1)}),
            (SystemExit, ('foo',), {},
                {'args' : ('foo',), 'code' : 'foo'}),
            (OSError, ('foo',), {},
                {'args' : ('foo',), 'filename' : None, 'filename2' : None,
                 'errno' : None, 'strerror' : None}),
            (OSError, ('foo', 'bar'), {},
                {'args' : ('foo', 'bar'),
                 'filename' : None, 'filename2' : None,
                 'errno' : 'foo', 'strerror' : 'bar'}),
            (OSError, ('foo', 'bar', 'baz'), {},
                {'args' : ('foo', 'bar'),
                 'filename' : 'baz', 'filename2' : None,
                 'errno' : 'foo', 'strerror' : 'bar'}),
            (OSError, ('foo', 'bar', 'baz', None, 'quux'), {},
                {'args' : ('foo', 'bar'), 'filename' : 'baz', 'filename2': 'quux'}),
            (OSError, ('errnoStr', 'strErrorStr', 'filenameStr'), {},
                {'args' : ('errnoStr', 'strErrorStr'),
                 'strerror' : 'strErrorStr', 'errno' : 'errnoStr',
                 'filename' : 'filenameStr'}),
            (OSError, (1, 'strErrorStr', 'filenameStr'), {},
                {'args' : (1, 'strErrorStr'), 'errno' : 1,
                 'strerror' : 'strErrorStr',
                 'filename' : 'filenameStr', 'filename2' : None}),
            (SyntaxError, (), {}, {'msg' : None, 'text' : None,
                'filename' : None, 'lineno' : None, 'offset' : None,
                'end_offset': None, 'print_file_and_line' : None}),
            (SyntaxError, ('msgStr',), {},
                {'args' : ('msgStr',), 'text' : None,
                 'print_file_and_line' : None, 'msg' : 'msgStr',
                 'filename' : None, 'lineno' : None, 'offset' : None,
                 'end_offset': None}),
            (SyntaxError, ('msgStr', ('filenameStr', 'linenoStr', 'offsetStr',
                           'textStr', 'endLinenoStr', 'endOffsetStr')), {},
                {'offset' : 'offsetStr', 'text' : 'textStr',
                 'args' : ('msgStr', ('filenameStr', 'linenoStr',
                                      'offsetStr', 'textStr',
                                      'endLinenoStr', 'endOffsetStr')),
                 'print_file_and_line' : None, 'msg' : 'msgStr',
                 'filename' : 'filenameStr', 'lineno' : 'linenoStr',
                 'end_lineno': 'endLinenoStr', 'end_offset': 'endOffsetStr'}),
            (SyntaxError, ('msgStr', 'filenameStr', 'linenoStr', 'offsetStr',
                           'textStr', 'endLinenoStr', 'endOffsetStr',
                           'print_file_and_lineStr'), {},
                {'text' : None,
                 'args' : ('msgStr', 'filenameStr', 'linenoStr', 'offsetStr',
                           'textStr', 'endLinenoStr', 'endOffsetStr',
                           'print_file_and_lineStr'),
                 'print_file_and_line' : None, 'msg' : 'msgStr',
                 'filename' : None, 'lineno' : None, 'offset' : None,
                 'end_lineno': None, 'end_offset': None}),
            (UnicodeError, (), {}, {'args' : (),}),
            (UnicodeEncodeError, ('ascii', 'a', 0, 1,
                                  'ordinal not in range'), {},
                {'args' : ('ascii', 'a', 0, 1,
                                           'ordinal not in range'),
                 'encoding' : 'ascii', 'object' : 'a',
                 'start' : 0, 'reason' : 'ordinal not in range'}),
            (UnicodeDecodeError, ('ascii', bytearray(b'\xff'), 0, 1,
                                  'ordinal not in range'), {},
                {'args' : ('ascii', bytearray(b'\xff'), 0, 1,
                                           'ordinal not in range'),
                 'encoding' : 'ascii', 'object' : b'\xff',
                 'start' : 0, 'reason' : 'ordinal not in range'}),
            (UnicodeDecodeError, ('ascii', b'\xff', 0, 1,
                                  'ordinal not in range'), {},
                {'args' : ('ascii', b'\xff', 0, 1,
                                           'ordinal not in range'),
                 'encoding' : 'ascii', 'object' : b'\xff',
                 'start' : 0, 'reason' : 'ordinal not in range'}),
            (UnicodeTranslateError, ("\u3042", 0, 1, "ouch"), {},
                {'args' : ('\u3042', 0, 1, 'ouch'),
                 'object' : '\u3042', 'reason' : 'ouch',
                 'start' : 0, 'end' : 1}),
            (NaiveException, ('foo',), {},
                {'args': ('foo',), 'x': 'foo'}),
            (SlottedNaiveException, ('foo',), {},
                {'args': ('foo',), 'x': 'foo'}),
            (AttributeError, ('foo',), dict(name='name', obj='obj'),
                dict(args=('foo',), name='name', obj='obj')),
        ]
        try:
            # More tests are in test_WindowsError
            exceptionList.append(
                (WindowsError, (1, 'strErrorStr', 'filenameStr'), {},
                    {'args' : (1, 'strErrorStr'),
                     'strerror' : 'strErrorStr', 'winerror' : None,
                     'errno' : 1,
                     'filename' : 'filenameStr', 'filename2' : None})
            )
        except NameError:
            pass

        for exc, args, kwargs, expected in exceptionList:
            try:
                e = exc(*args, **kwargs)
            except:
                print(f"\nexc={exc!r}, args={args!r}", file=sys.stderr)
                # raise
            else:
                # Verify module name
                if not type(e).__name__.endswith('NaiveException'):
                    self.assertEqual(type(e).__module__, 'builtins')
                # Verify no ref leaks in Exc_str()
                s = str(e)
                for checkArgName in expected:
                    value = getattr(e, checkArgName)
                    self.assertEqual(repr(value),
                                     repr(expected[checkArgName]),
                                     '%r.%s == %r, expected %r' % (
                                     e, checkArgName,
                                     value, expected[checkArgName]))

                # test for pickling support
                for p in [pickle]:
                    for protocol in range(p.HIGHEST_PROTOCOL + 1):
                        s = p.dumps(e, protocol)
                        new = p.loads(s)
                        for checkArgName in expected:
                            got = repr(getattr(new, checkArgName))
                            if exc == AttributeError and checkArgName == 'obj':
                                # See GH-103352, we're not pickling
                                # obj at this point. So verify it's None.
                                want = repr(None)
                            else:
                                want = repr(expected[checkArgName])
                            self.assertEqual(got, want,
                                             'pickled "%r", attribute "%s' %
                                             (e, checkArgName))