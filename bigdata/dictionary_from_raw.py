import re
import os
import json
import itertools


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
        self.counter = 0

    def to_struct(self):
        global_counter = itertools.count()

        return {
            "code": self.code,
            "name": self.name,
            "universe": self.universe,
            "elements": [
                element.to_struct(global_counter)
                for element in sorted(
                    self.entries + self.aggregates,
                    key=lambda entry: entry.index
                )
            ]
        }

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
            print(
                "BAD COUNT: %s  %d != %d" %
                (self.code, count, self.expected_items)
            )

    def _push_aggregate(self, rec):
        new_agg = Aggregate(
            self.counter, rec[1][0],
            int(rec[1][2]) if rec[1][2] else None)
        self.counter += 1
        if not self.current_aggregate:
            self.aggregates.append(new_agg)
        elif new_agg.level:
            l = new_agg.level - 1
            parent = self.aggregates[-1]
            while l - 1:
                parent = parent.children[-1]
                l -= 1

            parent.children.append(new_agg)
            new_agg.parent = parent

        elif self.current_aggregate.entries:
            parent = self.current_aggregate.parent
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
            to_repeat.copy_into(self, self.current_aggregate)
        else:
            assert False

    def _push_entry(self, entry):
        new_entry = Plain(
            self.counter, entry[1][0],
            int(entry[1][1]) if entry[1][1] else None)
        self.counter += 1
        if new_entry.level:
            level = new_entry.level
            l = level - 1
            parent = self.aggregates[-1]
            while l - 1:
                parent = parent.children[-1]
                l -= 1
            self.current_aggregate = parent

        if not self.current_aggregate:
            self.entries.append(new_entry)
        else:
            self.current_aggregate.entries.append(new_entry)

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

        for thing in sorted(
            self.entries + self.aggregates,
            key=lambda obj: obj.index
        ):
            text += thing._as_string(1)
        return text


class Aggregate(object):
    def __init__(self, index, name, level=None):
        self.index = index
        self.name = name
        self.parent = None
        self.level = level
        self.children = []
        self.entries = []

    def to_struct(self, global_counter):
        return {
            "index": self.index,
            "name": self.name,
            "global_counter": next(global_counter),
            "elements": [
                element.to_struct(global_counter)
                for element in sorted(
                    self.entries + self.children,
                    key=lambda entry: entry.index
                )
            ]
        }

    def _as_string(self, indent):
        text = "\n\n%s%s" % ("  " * indent, self.name)

        for thing in sorted(
            self.entries + self.children,
            key=lambda obj: obj.index
        ):
            text += thing._as_string(indent + 1)
        return text

    def _has_aggregate_entries(self):
        if self.entries:
            return True
        else:
            for ent in self.children:
                if ent._has_aggregate_entries():
                    return True
        return False

    def copy_into(self, matrix, agg):
        for thing in sorted(
            self.entries + self.children,
            key=lambda obj: obj.index
        ):
            if isinstance(thing, Plain):
                agg.entries.append(
                    Plain(matrix.counter, thing.name, thing.level)
                )
                matrix.counter += 1
            elif isinstance(thing, Aggregate):
                new_child = Aggregate(matrix.counter, thing.name, thing.level)
                agg.children.append(new_child)
                new_child.parent = agg
                matrix.counter += 1
                thing.copy_into(matrix, new_child)
            else:
                assert False


class Plain(object):
    def __init__(self, index, name, level=None):
        self.index = index
        self.name = name
        self.level = level

    def to_struct(self, global_counter):
        return {
            "index": self.index,
            "name": self.name,
            "global_counter": next(global_counter),
        }

    def _as_string(self, indent):
        return "\n%s%s" % ("  " * indent, self.name)


def _create_matrices(iter_):
    current_matrix = None
    for entry in iter_:
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
        re.compile(r"^HOUSING SUBJECTS \((?:SUMMARIZED|REPEATED)"),
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
            "aggregate",
            re.compile("^([L](\d)?\|)?([^\:]+\:[^\:]*)$"), (3, 1, 2)
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
            "plain", re.compile(r"^(?:L(\d)\|)?(.*)"), (2, 1)
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

    struct = []
    with open(fname) as fhandle:
        for rec in _parse(fhandle):
            #print(rec)
            struct.append(rec.to_struct())
    print(json.dumps(struct, indent=1))


if __name__ == '__main__':
    run()
