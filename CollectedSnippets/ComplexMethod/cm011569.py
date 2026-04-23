def __call__(self, ctx: _RendezvousContext, deadline: float) -> _Action:
        state = ctx.state

        # A closed rendezvous means that it no longer accepts new nodes.
        if state.closed:
            if ctx.node in state.redundancy_list:
                msg = f"The rendezvous '{ctx.settings.run_id}' is closed, terminating pending rendezvous."
                raise RendezvousGracefulExitError(msg)
            return _Action.ERROR_CLOSED

        if ctx.node in state.redundancy_list:
            msg = f"The node {ctx.node} is in redundancy list"
            logger.debug(msg)
            # don't apply the timeout logic here, since we want to allow the node to rejoin
            if len(state.participants) == ctx.settings.max_nodes:
                if _should_keep_alive(ctx):
                    return _Action.KEEP_ALIVE
                else:
                    return _Action.SYNC
            else:
                # transition to waiting state that will respect timeouts.
                msg = f"The node {ctx.node} is removed from redundancy list"
                logger.debug(msg)
                return _Action.REMOVE_FROM_REDUNDANCY_LIST

        is_participant = ctx.node in state.participants

        # If we are part of the rendezvous and it is already complete there is
        # no further action to take.
        if state.complete and is_participant:
            return _Action.FINISH

        now = time.monotonic()
        if now > deadline:
            rollback_period = 5  # 5 seconds

            # If we still have time to rollback (a short period on top of the
            # operation deadline), try to remove ourself from the rendezvous.
            # It is okay if we can't though as our keep-alive will eventually
            # expire.
            if now <= deadline + rollback_period:
                # If we are part of the rendezvous, it means we couldn't find
                # enough participants to complete it on time.
                if is_participant:
                    return _Action.REMOVE_FROM_PARTICIPANTS
                # If we are in the wait list, it means we couldn't wait till the
                # next round of the rendezvous.
                if ctx.node in state.wait_list:
                    return _Action.REMOVE_FROM_WAIT_LIST
            return _Action.ERROR_TIMEOUT

        if state.complete:
            # If we are here, it means we are not part of the rendezvous. In
            # case the rendezvous has capacity for additional participants add
            # ourself to the wait list for the next round.
            if len(state.participants) < ctx.settings.max_nodes:
                if ctx.node not in state.wait_list:
                    return _Action.ADD_TO_WAIT_LIST
            elif len(state.participants) >= ctx.settings.max_nodes:
                if (
                    ctx.node not in state.redundancy_list
                    and ctx.node not in state.wait_list
                ):
                    return _Action.ADD_TO_REDUNDANCY_LIST
        elif is_participant:
            # If the rendezvous has enough number of participants including us,
            # check whether we have passed the rendezvous deadline. If yes,
            # complete it.
            if (
                len(state.participants) >= ctx.settings.min_nodes
                and len(state.participants) <= ctx.settings.max_nodes
                and state.deadline is not None
            ):
                if state.deadline < datetime.now(timezone.utc):
                    msg = (
                        f"The node '{ctx.node}' marking the rendezvous complete, "
                        f"quorum established within deadline"
                    )
                    logger.debug(msg)
                    return _Action.MARK_RENDEZVOUS_COMPLETE
                else:
                    msg = f"The node '{ctx.node}' can't complete rendezvous: deadline reached"
                    logger.debug(msg)
            else:
                msg = f"The node '{ctx.node}' can't complete rendezvous: not enough participants"
                logger.debug(msg)
        else:
            # The rendezvous is not complete yet and we are not part of it. Try
            # to join.
            return _Action.ADD_TO_PARTICIPANTS

        if _should_keep_alive(ctx):
            return _Action.KEEP_ALIVE

        # At this point either the rendezvous is not complete, but we are part
        # of it, which means we have to wait for other participants to join; or
        # the rendezvous is complete, but we are not part of it, which means we
        # have to wait for the next round.
        return _Action.SYNC