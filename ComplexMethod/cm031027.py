def pendingcalls_wait(self, l, numadded, context = None):
        #now, stick around until l[0] has grown to 10
        count = 0
        while len(l) != numadded:
            #this busy loop is where we expect to be interrupted to
            #run our callbacks.  Note that some callbacks are only run on the
            #main thread
            if False and support.verbose:
                print("(%i)"%(len(l),),)
            for i in range(1000):
                a = i*i
            if context and not context.event.is_set():
                continue
            count += 1
            self.assertTrue(count < 10000,
                "timeout waiting for %i callbacks, got %i"%(numadded, len(l)))
        if False and support.verbose:
            print("(%i)"%(len(l),))