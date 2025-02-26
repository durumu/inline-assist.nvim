import textwrap
from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable


@dataclass
class Operation:
    # [start, end)
    offset_start: int
    offset_end: int
    lines: list[str]
    debug_info: str | None = None

    @classmethod
    def insert_before(cls, line_number: int, line: str):
        return cls(line_number, line_number, [line], "insert_before")

    @classmethod
    def delete(cls, start_lnum: int, end_lnum: int):
        return cls(start_lnum, end_lnum, [], "delete")

    @classmethod
    def replace_line(cls, line_number: int, line: str):
        return cls(line_number, line_number + 1, [line], "replace_line")

    def apply(self, buf: list[str], lnum: int = 0):
        buf[lnum + self.offset_start : lnum + self.offset_end] = self.lines


def hash_line(s: str) -> int:
    # TODO: stable hash?
    return hash(s.strip())


def stream_diff(
    original_lines: list[str], rewritten_lines: Iterable[str]
) -> Iterable[Operation]:
    hash_to_lnums = defaultdict(list)
    for i, line in enumerate(original_lines):
        if line.strip():  # if it isn't whitespace
            hash_to_lnums[hash_line(line)].append(i)

    buffer_lnum = 0
    net_lines_inserted = 0
    for line in rewritten_lines:
        stripped_line = line.strip()
        if (
            not stripped_line
            and buffer_lnum < len(original_lines)
            and not original_lines[buffer_lnum].strip()
        ):
            # Both lines are whitespace. Let's just replace.
            yield Operation.replace_line(buffer_lnum, line)
        elif occurrences := hash_to_lnums.get(hash_line(stripped_line)):
            first_original_occurrence = occurrences.pop(0) + net_lines_inserted
            # insertion_point = first_original_occurrence + offset
            if first_original_occurrence > buffer_lnum:
                yield Operation.delete(buffer_lnum, first_original_occurrence)
                net_lines_inserted -= first_original_occurrence - buffer_lnum
            yield Operation.replace_line(buffer_lnum, line)
        else:
            yield Operation.insert_before(buffer_lnum, line)
            net_lines_inserted += 1
        buffer_lnum += 1

    if buffer_lnum <= len(original_lines):
        yield Operation.delete(buffer_lnum, len(original_lines) + 1)


def test_insert():
    lines = ["a", "b", "c"]
    op = Operation.insert_before(2, "d")
    op.apply(lines)
    assert lines == ["a", "b", "d", "c"]


def test_delete():
    lines = ["a", "b", "c", "d"]
    op = Operation.delete(1, 3)
    op.apply(lines)
    assert lines == ["a", "d"]


def _test_diff(before: str, after: str):
    buf = before.splitlines()
    for op in stream_diff(before.splitlines(), after.splitlines()):
        print(op)
        op.apply(buf)
        print(*(f"~{line}" for line in buf), sep="\n")

    assert buf == after.splitlines()


def test_diff_noop():
    before = after = textwrap.dedent(
        """
        a
        """
    )

    _test_diff(before, after)


def test_diff_insert():
    before = textwrap.dedent(
        """
        def add_one(x):
            return x + 1
        """
    )

    after = textwrap.dedent(
        '''
        def add_one(x):
            """
            This is a docstring
            """
            return x + 1
        '''
    )

    _test_diff(before, after)


def test_diff_remove():
    before = textwrap.dedent(
        '''
        def add_one(x):
            """
            This is a docstring
            """
            return x + 1
        '''
    )

    after = textwrap.dedent(
        """
        def add_one(x):
            return x + 1
        """
    )

    _test_diff(before, after)


def test_diff_change():
    before = textwrap.dedent(
        """
        def accumulate(my_list):
            return sum(my_list)
        """
    )

    after = textwrap.dedent(
        """
        def accumulate(my_list):
            return max(my_list)
        """
    )

    _test_diff(before, after)


def test_diff_whitespace():
    before = textwrap.dedent(
        """
        def say_hi():
            if hi_enabled():
                print("hello")
            else:
                print("goodbye")
        """
    )

    after = textwrap.dedent(
        """
        def say_hi():
            print("hello")
        """
    )

    _test_diff(before, after)
