"""Guard for the single home of every tunable (params.py). Run: python -m pytest tests/

Fails when
  * two top-level names in params.py share a name,
  * a literal value defined in params.py reappears as a literal in any other .py file
    (a hand-typed second copy of a tunable), or
  * params.py contains something that looks like an email address (recipients and
    credentials belong in the environment, never in the parameter file).

Which literals are guarded: every str of 4 or more characters, every int of 5 or more
and every float, taken from the VALUES defined in params.py (dict keys excluded).
Shorter strings and small ints (0 to 4) are not guarded because they occur everywhere
for reasons that are not tunables (slice bounds, ranges, one-letter separators).

Escape hatch: tests/params_literal_allowlist.txt, one entry per line,
`path<TAB>repr-of-literal<TAB>reason`. It is empty by default; an entry without a
reason, or one that no longer matches a real literal, fails the build.
"""
import ast
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

import params  # noqa: E402

MIN_STR_LEN = 4
MIN_INT = 5
ALLOWLIST = os.path.join(REPO, 'tests', 'params_literal_allowlist.txt')
SKIP_DIRS = {'.git', '.github', 'tests', '__pycache__', 'venv', '.venv', 'node_modules'}


def _guarded(value):
    if isinstance(value, bool):
        return False
    if isinstance(value, str):
        return len(value) >= MIN_STR_LEN
    if isinstance(value, int):
        return abs(value) >= MIN_INT
    return isinstance(value, float)


def _leaves(value):
    """Scalar leaves of a parameter value; dict keys are not tunables."""
    if isinstance(value, dict):
        for v in value.values():
            yield from _leaves(v)
    elif isinstance(value, (list, tuple, set, frozenset)):
        for v in value:
            yield from _leaves(v)
    else:
        yield value


def guarded_literals(module):
    """{literal: [param names]} for every guarded literal defined in `module`."""
    out = {}
    for name in dir(module):
        if not name.isupper():
            continue
        for leaf in _leaves(getattr(module, name)):
            if _guarded(leaf):
                out.setdefault(leaf, []).append(name)
    return out


def duplicate_names(source):
    seen, dups = set(), set()
    for node in ast.parse(source).body:
        targets = []
        if isinstance(node, ast.Assign):
            targets = [t for t in node.targets if isinstance(t, ast.Name)]
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            targets = [node.target]
        for t in targets:
            (dups if t.id in seen else seen).add(t.id)
    return sorted(dups)


def _docstring_nodes(tree):
    ids = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            body = node.body
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
                ids.add(id(body[0].value))
    return ids


def find_violations(sources, guarded):
    """sources: {path: python text}. Returns [(path, line, literal, [param names])]."""
    found = []
    for path, text in sources.items():
        tree = ast.parse(text)
        docs = _docstring_nodes(tree)
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and id(node) not in docs and not isinstance(node.value, bool):
                if _guarded(node.value) and node.value in guarded:
                    found.append((path, node.lineno, node.value, guarded[node.value]))
    return found


def read_allowlist():
    entries = []
    if not os.path.exists(ALLOWLIST):
        return entries
    with open(ALLOWLIST, encoding='utf-8') as fh:
        for raw in fh:
            line = raw.rstrip('\n')
            if not line.strip() or line.lstrip().startswith('#'):
                continue
            parts = line.split('\t')
            assert len(parts) == 3 and parts[2].strip(), (
                f"allow-list entry needs path<TAB>repr<TAB>reason: {line!r}")
            entries.append((parts[0].strip(), parts[1].strip(), parts[2].strip()))
    return entries


def project_sources():
    sources = {}
    for dirpath, dirnames, filenames in os.walk(REPO):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith('.')]
        for fn in filenames:
            if fn.endswith('.py') and not (dirpath == REPO and fn == 'params.py'):
                path = os.path.join(dirpath, fn)
                with open(path, encoding='utf-8') as fh:
                    sources[os.path.relpath(path, REPO)] = fh.read()
    return sources


def test_params_names_are_unique():
    with open(os.path.join(REPO, 'params.py'), encoding='utf-8') as fh:
        assert duplicate_names(fh.read()) == []


def test_no_tunable_literal_is_retyped_outside_params():
    guarded = guarded_literals(params)
    # A guard that ran on a thin input would pass vacuously (checks-must-distinguish-unknown).
    assert len(guarded) >= 100, f"only {len(guarded)} guarded literals: params.py looks empty"
    sources = project_sources()
    assert 'main.py' in sources and any(p.startswith('scrapers') for p in sources), sources.keys()

    allowed = {(p, v) for p, v, _ in read_allowlist()}
    hits = find_violations(sources, guarded)
    used = {(p, repr(lit)) for p, _, lit, _ in hits}
    stale = sorted(a for a in allowed if a not in used)
    assert not stale, f"allow-list entries that match nothing: {stale}"

    bad = [h for h in hits if (h[0], repr(h[2])) not in allowed]
    assert not bad, "literal(s) from params.py retyped outside it:\n" + "\n".join(
        f"  {p}:{ln}: {lit!r} (params: {', '.join(names)})" for p, ln, lit, names in bad)


def test_guard_detects_a_retyped_literal():
    """Positive control: the guard must go red on a hand-typed second copy."""
    guarded = guarded_literals(params)
    horizon_like = params.BARBICAN_BASE_URL
    hits = find_violations({'x.py': f'URL = "{horizon_like}"\n'}, guarded)
    assert [h[3] for h in hits] == [['BARBICAN_BASE_URL']]
    # a docstring mentioning the value is not a literal use
    assert find_violations({'x.py': f'"""{horizon_like}"""\n'}, guarded) == []


def test_guard_detects_duplicate_names():
    assert duplicate_names("A = 1\nB = 2\nA = 3\n") == ['A']
    assert duplicate_names("A = 1\nB = 2\n") == []


def test_params_holds_no_email_address():
    with open(os.path.join(REPO, 'params.py'), encoding='utf-8') as fh:
        text = fh.read()
    assert re.search(r'[\w.+-]+@[\w-]+\.[\w.-]+', text) is None
    assert re.search(r'[\w.+-]+@[\w-]+\.[\w.-]+', 'someone@example.org')  # the pattern can fire


def test_allowlist_is_empty_or_every_entry_has_a_reason():
    for _path, _lit, reason in read_allowlist():
        assert reason
