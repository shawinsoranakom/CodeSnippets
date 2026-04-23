def test_exc(formatstr, args, exception, excmsg):
    try:
        testformat(formatstr, args)
    except exception as exc:
        if str(exc) == excmsg:
            if verbose:
                print("yes")
        else:
            if verbose: print('no')
            print('Unexpected ', exception, ':', repr(str(exc)))
            raise
    except:
        if verbose: print('no')
        print('Unexpected exception')
        raise
    else:
        raise TestFailed('did not get expected exception: %s' % excmsg)