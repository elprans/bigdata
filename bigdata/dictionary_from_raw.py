import re
import os


def _ignores(iter_):
    ignore = [
        re.compile(r"^Chapter"),
        re.compile(r"^Summary Table Outlines"),
        re.compile(r".*Summary Table Outlines\s*$"),
        re.compile(r"^POPULATION SUBJECTS"),
        re.compile(r"^U.S. Census Bureau, Census 2000"),
        re.compile(r".*—Con.$"),
    ]

    for line in iter_:
        for reg in ignore:
            if reg.match(line):
                break
        else:
            yield line


def _chops(iter_):
    return (l.rstrip() for l in iter_)


def _derive_tokens(iter_):

    matches = [
        (
            "matrix_desc_full",
            re.compile(
                r"^([A-Z]+[0-9]+[A-Z]*)\."
                "\s+([A-Z0-9 \-,’\(\))]+)"
                "\ \[(\d+)\]"
                "(?:\ \(FINAL\ NATIONAL\ FILE\ ONLY\))?$", re.X),
            (1, 2, 3)
        ),

        (
            "matrix_desc_left",
            re.compile(
                r"^([A-Z]+[0-9]+[A-Z]*)\."
                "\s+([A-Z0-9 \-,’\(\)]+)$", re.X),
            (1, 2)
        ),

        (
            "matrix_desc_right",
            re.compile(
                r"^([A-Z0-9 -,]+) \[(\d+)\]$", re.X),
            (1, 2)
        ),

        (
            "universe", re.compile("^Universe: (.+)$"), (1,)
        ),

        (
            "aggregate", re.compile("^([A-Z][a-z]+)\:([\:]*)$"), (1, 2)
        ),

        (
            "aggregate_right", re.compile("^([a-z]+)\:([\:]*)$"), (1, 2)
        ),

        (
            "repeat", re.compile(r"^\(Repeat [A-Z]+\)$"), (0,)
        ),

        (
            "ends_in_trailer", re.compile(r".*[;\-,]$"), (0,)
        ),

        (
            "continuation", re.compile(r"^[a-z].*$"), (0, )
        ),

        (
            "ellipses", re.compile(r"^\.$"), (0, )
        ),

        (
            "plain", re.compile(r".*"), (0, )
        )


    ]

    for line in iter_:
        for name, reg, indexes in matches:
            m = reg.match(line)
            if m:
                groups = m.group(*indexes)
                if len(indexes) == 1:
                    groups = (groups,)
                yield (name, groups)
                break


def _merge_continuations(iter_):
    buf = []
    while True:
        try:
            rec = next(iter_)

            if rec[0] == "continuation":
                continuation_text = rec[1][0]
                assert buf
                #import pdb
                #pdb.set_trace()
                buf[-1] = (
                    buf[-1][0], (buf[-1][1][0] + " " + continuation_text,) +
                    buf[-1][1][1:])
            else:
                buf.append(rec)
        except StopIteration:
            break
    while buf:
        yield buf.pop(0)


def _combine_tokens(iter_):
    buf = []
    while True:
        try:
            rec = next(iter_)

            if rec[0] in (
                    "matrix_desc_full", "universe", "repeat", "aggregate"):
                while buf:
                    brec = buf.pop(0)
                    if brec[0] != 'matrix_desc_left':
                        yield brec
                yield rec
            elif rec[0] == "matrix_desc_left":
                buf.append(rec)
            elif rec[0] == "matrix_desc_right":
                text = rec[1][0]
                code = None
                while buf:
                    prev = buf.pop(-1)
                    if prev[0] == "matrix_desc_left":
                        text = prev[1][1] + " " + text
                        code = prev[1][0]
                        break
                    else:
                        text = prev[1][0] + " " + text

                size = rec[1][1]
                if not code:
                    raise Exception("couldn't get code for left/right matrix")
                newrec = ("matrix_desc_full", (code, text, size))
                while buf:
                    brec = buf.pop(0)
                    if brec[0] != 'matrix_desc_left':
                        yield brec
                yield newrec
            elif rec[0] == "aggregate_right":
                text = rec[1][0]
                while buf:
                    prev = buf.pop(-1)
                    if prev[0] in ("ends_in_trailer", "plain"):
                        text = prev[1][0] + text
                    else:
                        break
                while buf:
                    brec = buf.pop(0)
                    if brec[0] != 'matrix_desc_left':
                        yield brec
                newrec = ("aggregate", (text, ""))
                yield newrec
            elif rec[0] == "ends_in_trailer":
                buf.append(rec)
            elif rec[0] == "plain":
                buf.append(rec)

        except StopIteration:
            break


def _parse(fh):

    iter_ = _chops(fh)
    iter_ = _ignores(iter_)
    iter_ = _derive_tokens(iter_)
    iter_ = _merge_continuations(iter_)
    iter_ = _combine_tokens(iter_)
    for line in iter_:
        yield line


def run():
    fname = os.path.join(
        os.path.dirname(__file__), "..", "data", "raw_text_grab.txt")

    with open(fname) as fhandle:
        for rec in _parse(fhandle):
            print(rec)


if __name__ == '__main__':
    run()
