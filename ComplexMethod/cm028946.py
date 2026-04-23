def _unnumber_chaps_and_secs(lines):
    def _startswith_unnumbered(l):
        UNNUMBERED = {'\\section{小结',
                      '\\section{练习',
                      '\\subsection{小结',
                      '\\subsection{练习'}
        for unnum in UNNUMBERED:
            if l.startswith(unnum):
                return True
        return False

    # Preface, Installation, and Notation are unnumbered chapters
    NUM_UNNUMBERED_CHAPS = 3
    # Prelimilaries
    TOC2_START_CHAP_NO = 5

    preface_reached = False
    ch2_reached = False
    num_chaps = 0
    for i, l in enumerate(lines):
        if l.startswith('\\chapter{'):
            num_chaps += 1
            # Unnumber unnumbered chapters
            if num_chaps <= NUM_UNNUMBERED_CHAPS:
                chap_name = re.split('{|}', l)[1]
                lines[i] = ('\\chapter*{' + chap_name
                            + '}\\addcontentsline{toc}{chapter}{'
                            + chap_name + '}\n')
            # Set tocdepth to 2 after Chap 1
            elif num_chaps == TOC2_START_CHAP_NO:
                lines[i] = ('\\addtocontents{toc}{\\protect\\setcounter{tocdepth}{2}}\n'
                            + lines[i])
        # Unnumber all sections in unnumbered chapters
        elif 1 <= num_chaps <= NUM_UNNUMBERED_CHAPS:
            if (l.startswith('\\section') or l.startswith('\\subsection')
                    or l.startswith('\\subsubsection')):
                lines[i] = l.replace('section{', 'section*{')
        # Unnumber summary, references, exercises, qr code in numbered chapters
        elif _startswith_unnumbered(l):
            lines[i] = l.replace('section{', 'section*{')
    # Since we inserted '\n' in some lines[i], re-build the list
    lines = '\n'.join(lines).split('\n')