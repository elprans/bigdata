import re
import os


class Matrix(object):
    def __init__(self, rec):
        self.code = rec[1][0]
        self.name = rec[1][1]
        self.expected_items = int(rec[1][2])
        self.universe = None
        self.aggregates = []
        self.entries = []
        self.current_aggregate = None
        self.scale = None

    def confirm(self):
        count = 0

        stack = list(self.aggregates)
        while stack:
            agg = stack.pop(0)
            count += 1
            count += len(agg.entries)
            stack.extend(agg.children)

        count += len(self.entries)

        if count != self.expected_items:
            print "BAD COUNT: %s  %d != %d" % (self.code, count, self.expected_items)
            #if self.code == "PCT17D":
            #    import pdb
            #    pdb.set_trace()
        #assert count == self.expected_items

    def _push_aggregate(self, rec):
        new_agg = Aggregate(self, rec[1][0], rec[1][1] == 'N|')
        if not self.current_aggregate:
            self.aggregates.append(new_agg)
        elif not new_agg.nest and self.current_aggregate.entries:
            # sibling case

            parent = self.current_aggregate.parent
            #while parent is not None and parent.entries:
            #    parent = parent.parent

            new_agg.parent = parent
            if new_agg.parent is None:
                self.aggregates.append(new_agg)
            else:
                parent.children.append(new_agg)
        else:
            new_agg.parent = self.current_aggregate
            self.current_aggregate.children.append(new_agg)
        self.current_aggregate = new_agg

    def _push_repeat(self, rec):
        if self.current_aggregate.parent:
            to_repeat = self.current_aggregate.parent.children[-2]
            to_repeat.copy_into(self.current_aggregate)
        else:
            assert False

    def _push_entry(self, entry):
        if not self.current_aggregate:
            self.entries.append(entry[1][0])
        else:
            self.current_aggregate.entries.append(entry[1][0])

    def receive_rec(self, rec):
        if rec[0] == 'universe':
            self.universe = rec[1][0]
        elif rec[0] == 'scale':
            self.scale = rec[1][0]
        elif rec[0] == 'aggregate':
            self._push_aggregate(rec)
        elif rec[0] == 'plain':
            self._push_entry(rec)
        elif rec[0] == 'repeat':
            self._push_repeat(rec)
        else:
            assert False

    def __str__(self):
        text = "\n%s: %s [%s]" % (self.code, self.name, self.expected_items)
        for entry in self.entries:
            text += "\n %s" % entry
        for agg in self.aggregates:
            text += agg._as_string(1)
        return text


class Aggregate(object):
    def __init__(self, matrix, name, nest=False):
        self.matrix = matrix
        self.name = name
        self.parent = None
        self.nest = nest
        self.children = []
        self.entries = []

    def _as_string(self, indent):
        text = "\n\n%s%s" % ("  " * indent, self.name)
        for entry in self.entries:
            text += "\n%s%s" % ("  " * (indent + 1), entry)
        for agg in self.children:
            text += agg._as_string(indent + 1)
        return text

    def _has_aggregate_entries(self):
        if self.entries:
            return True
        else:
            for ent in self.children:
                if ent._has_aggregate_entries():
                    return True
        return False

    def copy_into(self, agg):
        agg.entries.extend(self.entries)
        for child in self.children:
            new_child = Aggregate(self.matrix, child.name)
            new_child.parent = agg
            agg.children.append(new_child)
            child.copy_into(new_child)


def _create_matrices(iter_):
    current_matrix = None
    for entry in iter_:
        #print entry
        if entry[0] == 'matrix_desc_full':
            if current_matrix is not None:
                current_matrix.confirm()
                yield current_matrix
            current_matrix = Matrix(entry)
        else:
            current_matrix.receive_rec(entry)
    if current_matrix:
        yield current_matrix


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
            "aggregate", re.compile("^(N\|)?([^\:]+\:[^\:]*)$"), (2, 1)
        ),

        (
            "repeat", re.compile(r"^\(Repeat [A-Z ]+\)$"), (0,)
        ),

        (
            "ends_in_trailer", re.compile(r".*[;\-,]$"), (0,)
        ),
        (
            "continuation", re.compile(r"^[a-z].*$"), (0, )
        ),
        (
            "continuation", re.compile(r"^C\|(.*)$"), (1, )
        ),

        (
            "ellipses", re.compile(r"^\.$"), (0, )
        ),

        (
            "scale", re.compile(r".*—$"), (0,)
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
                buf[-1] = (
                    buf[-1][0], (buf[-1][1][0] + " " + continuation_text,) +
                    buf[-1][1][1:])
            else:
                buf.append(rec)
        except StopIteration:
            break
    while buf:
        yield buf.pop(0)


def _merge_ends_in_trailer(iter_):
    buf = []
    while True:
        try:
            rec = next(iter_)
            if rec[0] == "ends_in_trailer":
                buf.append(rec)
                continue
            elif buf:
                assert rec[0] == 'plain'
                text = ""
                while buf:
                    etrec = buf.pop(0)
                    text += etrec[1][0] + " "
                text += rec[1][0]
                rec = (
                    rec[0], (text, ) + rec[1][1:]
                )

            yield rec
        except StopIteration:
            break
    assert not buf


def _fill_ellipses(iter_):
    rec = None
    while True:
        try:
            lastrec = rec
            rec = next(iter_)
            if rec[0] == 'ellipses':
                m = re.match(r'(\d+) (.*)$', lastrec[1][0])
                startnum = int(m.group(1))
                desc = m.group(2)

                e2, e3 = next(iter_), next(iter_)
                assert e2[0] == e3[0] == 'ellipses'

                contrec = next(iter_)
                m = re.match(r'(\d+) (.*)$', contrec[1][0])
                endnum = int(m.group(1))
                assert m.group(2) == desc

                for dig in range(startnum + 1, endnum):
                    yield (
                        lastrec[0],
                        ("%d %s" % (dig, desc), ) + lastrec[1][1:]
                    )
                yield contrec
            else:
                yield rec
        except StopIteration:
            break


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
    iter_ = _merge_ends_in_trailer(iter_)
    iter_ = _fill_ellipses(iter_)
    iter_ = _combine_tokens(iter_)
    iter_ = _create_matrices(iter_)
    for rec in iter_:
        yield rec


def run():
    fname = os.path.join(
        os.path.dirname(__file__), "..", "data", "raw_text_grab.txt")

    with open(fname) as fhandle:
        for rec in _parse(fhandle):
            pass
            print(rec)


if __name__ == '__main__':
    run()
