"""Splits a token stream into reasoning and answer, even when a tag is cut across two chunks."""
OPEN, CLOSE = "<think>", "</think>"


def _partial_suffix(buf: str, tag: str) -> int:
    """Length of the longest proper prefix of `tag` that `buf` ends with (it might be a tag still arriving)."""
    for k in range(min(len(tag) - 1, len(buf)), 0, -1):
        if buf.endswith(tag[:k]):
            return k
    return 0


class ThinkingSplitter:
    def __init__(self, prefilled: bool = False):
        self.buf = ""
        self.in_think = prefilled

    def feed(self, text: str) -> list[tuple[str, str]]:
        self.buf += text
        out: list[tuple[str, str]] = []
        while True:
            kind = "reasoning" if self.in_think else "content"
            tag = CLOSE if self.in_think else OPEN
            idx = self.buf.find(tag)
            if idx >= 0:
                if idx:
                    out.append((kind, self.buf[:idx]))
                self.buf = self.buf[idx + len(tag):]
                self.in_think = not self.in_think
                continue
            hold = _partial_suffix(self.buf, tag)
            emit = self.buf[: len(self.buf) - hold]
            if emit:
                out.append((kind, emit))
            self.buf = self.buf[len(self.buf) - hold:]
            return out

    def flush(self) -> list[tuple[str, str]]:
        rest, self.buf = self.buf, ""
        return [("reasoning" if self.in_think else "content", rest)] if rest else []
