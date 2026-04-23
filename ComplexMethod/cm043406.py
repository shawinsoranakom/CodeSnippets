def _emit_js(self, cmd: Cmd) -> str:
        op, a = cmd.op, cmd.args
        if op == "GO":         return f"window.location.href = '{a[0]}';"
        if op == "RELOAD":     return "window.location.reload();"
        if op == "BACK":       return "window.history.back();"
        if op == "FORWARD":    return "window.history.forward();"

        if op == "WAIT":
            arg, kind = a[0]
            timeout   = a[1] or 10
            if kind == "seconds":
                return f"await new Promise(r=>setTimeout(r,{arg}*1000));"
            if kind == "selector":
                sel = arg.replace("\\","\\\\").replace("'","\\'")
                return textwrap.dedent(f"""
                    await new Promise((res,rej)=>{{
                      const max = {timeout*1000}, t0 = performance.now();
                      const id = setInterval(()=>{{
                        if(document.querySelector('{sel}')){{clearInterval(id);res();}}
                        else if(performance.now()-t0>max){{clearInterval(id);rej('WAIT selector timeout');}}
                      }},100);
                    }});
                """).strip()
            if kind == "text":
                txt = arg.replace('`', '\\`')
                return textwrap.dedent(f"""
                    await new Promise((res,rej)=>{{
                      const max={timeout*1000},t0=performance.now();
                      const id=setInterval(()=>{{
                        if(document.body.innerText.includes(`{txt}`)){{clearInterval(id);res();}}
                        else if(performance.now()-t0>max){{clearInterval(id);rej('WAIT text timeout');}}
                      }},100);
                    }});
                """).strip()

        # click-style helpers
        def _js_click(sel, evt="click", button=0, detail=1):
            sel = sel.replace("'", "\\'")
            return textwrap.dedent(f"""
                (()=>{{
                  const el=document.querySelector('{sel}');
                  if(el){{
                    el.focus&&el.focus();
                    el.dispatchEvent(new MouseEvent('{evt}',{{bubbles:true,button:{button},detail:{detail}}}));
                  }}
                }})();
            """).strip()

        def _js_click_xy(x, y, evt="click", button=0, detail=1):
            return textwrap.dedent(f"""
                (()=>{{
                  const el=document.elementFromPoint({x},{y});
                  if(el){{
                    el.focus&&el.focus();
                    el.dispatchEvent(new MouseEvent('{evt}',{{bubbles:true,button:{button},detail:{detail}}}));
                  }}
                }})();
            """).strip()

        if op in ("CLICK", "DBLCLICK", "RIGHTCLICK"):
            evt   = {"CLICK":"click","DBLCLICK":"dblclick","RIGHTCLICK":"contextmenu"}[op]
            btn   = 2 if op=="RIGHTCLICK" else 0
            det   = 2 if op=="DBLCLICK"   else 1
            kind,*rest = a[0]
            return _js_click_xy(*rest) if kind=="coords" else _js_click(rest[0],evt,btn,det)

        if op == "MOVE":
            _, x, y = a[0]
            return textwrap.dedent(f"""
                document.dispatchEvent(new MouseEvent('mousemove',{{clientX:{x},clientY:{y},bubbles:true}}));
            """).strip()

        if op == "DRAG":
            (_, x1, y1), (_, x2, y2) = a
            return textwrap.dedent(f"""
                (()=>{{
                  const s=document.elementFromPoint({x1},{y1});
                  if(!s) return;
                  s.dispatchEvent(new MouseEvent('mousedown',{{bubbles:true,clientX:{x1},clientY:{y1}}}));
                  document.dispatchEvent(new MouseEvent('mousemove',{{bubbles:true,clientX:{x2},clientY:{y2}}}));
                  document.dispatchEvent(new MouseEvent('mouseup',  {{bubbles:true,clientX:{x2},clientY:{y2}}}));
                }})();
            """).strip()

        if op == "SCROLL":
            dir_, amt = a
            dx, dy = {"UP":(0,-amt),"DOWN":(0,amt),"LEFT":(-amt,0),"RIGHT":(amt,0)}[dir_]
            return f"window.scrollBy({dx},{dy});"

        if op == "TYPE":
            txt = a[0].replace("'", "\\'")
            return textwrap.dedent(f"""
                (()=>{{
                  const el=document.activeElement;
                  if(el){{
                    el.value += '{txt}';
                    el.dispatchEvent(new Event('input',{{bubbles:true}}));
                  }}
                }})();
            """).strip()

        if op == "CLEAR":
            sel = a[0].replace("'", "\\'")
            return textwrap.dedent(f"""
                (()=>{{
                  const el=document.querySelector('{sel}');
                  if(el && 'value' in el){{
                    el.value = '';
                    el.dispatchEvent(new Event('input',{{bubbles:true}}));
                    el.dispatchEvent(new Event('change',{{bubbles:true}}));
                  }}
                }})();
            """).strip()

        if op == "SET" and len(a) == 2:
            # This is SET for input fields (SET `#field` "value")
            sel = a[0].replace("'", "\\'")
            val = a[1].replace("'", "\\'")
            return textwrap.dedent(f"""
                (()=>{{
                  const el=document.querySelector('{sel}');
                  if(el && 'value' in el){{
                    el.value = '';
                    el.focus&&el.focus();
                    el.value = '{val}';
                    el.dispatchEvent(new Event('input',{{bubbles:true}}));
                    el.dispatchEvent(new Event('change',{{bubbles:true}}));
                  }}
                }})();
            """).strip()

        if op in ("PRESS","KEYDOWN","KEYUP"):
            key = a[0]
            evs = {"PRESS":("keydown","keyup"),"KEYDOWN":("keydown",),"KEYUP":("keyup",)}[op]
            return ";".join([f"document.dispatchEvent(new KeyboardEvent('{e}',{{key:'{key}',bubbles:true}}))" for e in evs]) + ";"

        if op == "EVAL":
            return textwrap.dedent(f"""
                (()=>{{
                  try {{
                    {a[0]};
                  }} catch (e) {{
                    console.error('C4A-Script EVAL error:', e);
                  }}
                }})();
            """).strip()

        if op == "IF":
            condition, then_cmd, else_cmd = a

            # Generate condition JavaScript
            js_condition = self._emit_condition(condition)

            # Generate commands - handle both regular commands and procedure calls
            then_js = self._handle_cmd_or_proc(then_cmd)
            else_js = self._handle_cmd_or_proc(else_cmd) if else_cmd else ""

            if else_cmd:
                return textwrap.dedent(f"""
                    if ({js_condition}) {{
                      {then_js}
                    }} else {{
                      {else_js}
                    }}
                """).strip()
            else:
                return textwrap.dedent(f"""
                    if ({js_condition}) {{
                      {then_js}
                    }}
                """).strip()

        if op == "REPEAT":
            cmd, count = a

            # Handle the count - could be number or JS expression
            if count.isdigit():
                # Simple number
                repeat_js = self._handle_cmd_or_proc(cmd)
                return textwrap.dedent(f"""
                    for (let _i = 0; _i < {count}; _i++) {{
                      {repeat_js}
                    }}
                """).strip()
            else:
                # JS expression (from backticks)
                count_expr = count[1:-1] if count.startswith('`') and count.endswith('`') else count
                repeat_js = self._handle_cmd_or_proc(cmd)
                return textwrap.dedent(f"""
                    (()=>{{
                      const _count = {count_expr};
                      if (typeof _count === 'number') {{
                        for (let _i = 0; _i < _count; _i++) {{
                          {repeat_js}
                        }}
                      }} else if (_count) {{
                        {repeat_js}
                      }}
                    }})();
                """).strip()

        raise ValueError(f"Unhandled op {op}")