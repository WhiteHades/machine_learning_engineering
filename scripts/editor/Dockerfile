# syntax=docker/dockerfile:1
ARG BOOK_BASE_IMAGE
FROM rust:1.94-bookworm AS parser-builder
RUN cargo install tree-sitter-cli --version 0.27.0 --locked

FROM ${BOOK_BASE_IMAGE}

# The book's scientific packages remain at their existing versions.
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl git build-essential unzip ripgrep fd-find nodejs imagemagick \
    && ln -s /usr/bin/fdfind /usr/local/bin/fd \
    && rm -rf /var/lib/apt/lists/*
RUN curl -fsSL https://github.com/neovim/neovim/releases/download/v0.12.5/nvim-linux-x86_64.tar.gz -o /tmp/nvim.tar.gz \
    && echo 'bce0f56eda1f1b1db6eee8f4133d7a38813ea07933837dd1777411ca384c6875  /tmp/nvim.tar.gz' | sha256sum -c - \
    && tar -C /opt -xzf /tmp/nvim.tar.gz && rm /tmp/nvim.tar.gz \
    && ln -s /opt/nvim-linux-x86_64/bin/nvim /usr/local/bin/nvim
COPY --from=parser-builder /usr/local/cargo/bin/tree-sitter /usr/local/bin/tree-sitter
RUN python -m pip freeze > /tmp/book-constraints.txt \
    && python -m pip install --no-cache-dir -c /tmp/book-constraints.txt \
       pynvim==0.6.0 jupytext==1.19.5 pyright==1.1.414 ruff==0.16.7 \
    && python -m pip check && rm /tmp/book-constraints.txt

# Keep all URI validators, but build each parser only when it is first used.
# This dependency otherwise builds dozens of unused parsers on every import.
RUN python - <<'PY'
import importlib.util
from pathlib import Path

spec = importlib.util.find_spec("rfc3987_syntax")
if spec is not None:
    import rfc3987_syntax.syntax_helpers as original
    path = Path(original.__file__)
    source = path.read_text()
    old = '''    parser = Lark(grammar, start=rule_name, parser=RFC3987_SYNTAX_PARSER_TYPE)

    def syntax_validator(text):
'''
    new = '''    parser = None

    def syntax_validator(text):
        nonlocal parser
        if parser is None:
            parser = Lark(grammar, start=rule_name, parser=RFC3987_SYNTAX_PARSER_TYPE)
'''
    assert source.count(old) == 1, "review rfc3987_syntax before updating this patch"
    source = source.replace(old, new)
    patched = dict(original.__dict__)
    exec(compile(source, str(path), "exec"), patched)
    for name in vars(original):
        if name.startswith("is_valid_syntax_"):
            for value in ("", "a", "123", "::1", "https://example.org/a?q=1#x", "https://例え.jp/", "bad space", "\n", "%20", "%zz"):
                assert patched[name](value) == getattr(original, name)(value), (name, value)
    path.write_text(source)
PY
