def _iter_close_tests(self, verbose=False):
        i = 0
        for actions in self.iter_action_sets():
            print()
            for fix in self.iter_fixtures():
                i += 1
                if i > 1000:
                    return
                if verbose:
                    if (i - 1) % 6 == 0:
                        print()
                    print(i, fix, '({} actions)'.format(len(actions)))
                else:
                    if (i - 1) % 6 == 0:
                        print(' ', end='')
                    print('.', end=''); sys.stdout.flush()
                yield i, fix, actions
            if verbose:
                print('---')
        print()