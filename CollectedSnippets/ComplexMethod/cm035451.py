def get_agent_obs_text(obs: BrowserOutputObservation) -> str:
    """Get a concise text that will be shown to the agent."""
    if obs.trigger_by_action == ActionType.BROWSE_INTERACTIVE:
        text = f'[Current URL: {obs.url}]\n'
        text += f'[Focused element bid: {obs.focused_element_bid}]\n'

        # Add screenshot path information if available
        if obs.screenshot_path:
            text += f'[Screenshot saved to: {obs.screenshot_path}]\n'

        text += '\n'

        if obs.error:
            text += (
                '================ BEGIN error message ===============\n'
                'The following error occurred when executing the last action:\n'
                f'{obs.last_browser_action_error}\n'
                '================ END error message ===============\n'
            )
        else:
            text += '[Action executed successfully.]\n'
        try:
            # We do not filter visible only here because we want to show the full content
            # of the web page to the agent for simplicity.
            # FIXME: handle the case when the web page is too large
            cur_axtree_txt = get_axtree_str(
                obs.axtree_object,
                obs.extra_element_properties,
                filter_visible_only=obs.filter_visible_only,
            )
            if not obs.filter_visible_only:
                text += (
                    f'Accessibility tree of the COMPLETE webpage:\nNote: [bid] is the unique alpha-numeric identifier at the beginning of lines for each element in the AXTree. Always use bid to refer to elements in your actions.\n'
                    f'============== BEGIN accessibility tree ==============\n'
                    f'{cur_axtree_txt}\n'
                    f'============== END accessibility tree ==============\n'
                )
            else:
                text += (
                    f'Accessibility tree of the VISIBLE portion of the webpage (accessibility tree of complete webpage is too large and you may need to scroll to view remaining portion of the webpage):\nNote: [bid] is the unique alpha-numeric identifier at the beginning of lines for each element in the AXTree. Always use bid to refer to elements in your actions.\n'
                    f'============== BEGIN accessibility tree ==============\n'
                    f'{cur_axtree_txt}\n'
                    f'============== END accessibility tree ==============\n'
                )
        except Exception as e:
            text += f'\n[Error encountered when processing the accessibility tree: {e}]'
        return text

    elif obs.trigger_by_action == ActionType.BROWSE:
        text = f'[Current URL: {obs.url}]\n'

        if obs.error:
            text += (
                '================ BEGIN error message ===============\n'
                'The following error occurred when trying to visit the URL:\n'
                f'{obs.last_browser_action_error}\n'
                '================ END error message ===============\n'
            )
        text += '============== BEGIN webpage content ==============\n'
        text += obs.content
        text += '\n============== END webpage content ==============\n'
        return text
    else:
        raise ValueError(f'Invalid trigger_by_action: {obs.trigger_by_action}')