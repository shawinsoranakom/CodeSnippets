def handler(event, lists = lists,
                    mc_type = mc_type, mc_state = mc_state,
                    ishandlerrunning = self.ishandlerrunning,
                    doafterhandler = self.doafterhandler):
            ishandlerrunning[:] = [True]
            event.mc_type = mc_type
            event.mc_state = mc_state
            wascalled = {}
            r = None
            for l in lists:
                for i in range(len(l)-1, -1, -1):
                    func = l[i]
                    if func not in wascalled:
                        wascalled[func] = True
                        r = l[i](event)
                        if r:
                            break
                if r:
                    break
            ishandlerrunning[:] = []
            # Call all functions in doafterhandler and remove them from list
            for f in doafterhandler:
                f()
            doafterhandler[:] = []
            if r:
                return r