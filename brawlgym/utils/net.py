"""
HTTP GET/HEAD that still works where Python cannot verify a server's TLS chain.

Python's ssl module checks against the root certificates only. Windows also fetches missing
intermediate certificates, so some CDN edges fail verification in Python while the OS accepts
them. On that failure the request is repeated through Windows' own curl.exe, which uses the OS
certificate store.
"""
from __future__ import annotations

import os
import ssl
import subprocess
import urllib.error
import urllib.request
from typing import Dict, Optional, Tuple

USER_AGENT = "brawlgym"


def _curl(url: str, head: bool, timeout: float, headers: Dict[str, str]) -> Tuple[Dict[str, str], bytes]:
    curl = os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "System32", "curl.exe")
    cmd = [curl, "-sSL", "--max-time", str(int(timeout))]
    for k, v in headers.items():
        cmd += ["-H", "%s: %s" % (k, v)]
    cmd += ["-I"] if head else ["-D", "-"]           # headers of every hop, then the body
    out = subprocess.run(cmd + [url], capture_output=True, timeout=timeout + 15)
    if out.returncode != 0:
        raise urllib.error.URLError("curl.exe failed (%d): %s"
                                    % (out.returncode, out.stderr.decode(errors="replace").strip()))
    raw, pos, last = out.stdout, 0, ""
    while raw.startswith(b"HTTP/", pos):
        end = raw.index(b"\r\n\r\n", pos) + 4
        last, pos = raw[pos:end].decode("iso-8859-1"), end
    lines = last.split("\r\n")
    status = int(lines[0].split()[1])
    if status >= 400:
        raise urllib.error.HTTPError(url, status, lines[0], None, None)
    found = {k.strip().lower(): v.strip() for k, _s, v in (ln.partition(":") for ln in lines[1:] if ":" in ln)}
    return found, b"" if head else raw[pos:]


def fetch(url: str, head: bool = False, timeout: float = 60.0,
          headers: Optional[Dict[str, str]] = None) -> Tuple[Dict[str, str], bytes]:
    """
    (lowercased response headers, body) for a GET, or a HEAD with an empty body. HTTP errors raise
    urllib.error.HTTPError either way.
    """
    headers = dict({"User-Agent": USER_AGENT}, **(headers or {}))
    req = urllib.request.Request(url, method="HEAD" if head else "GET", headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return {k.lower(): v for k, v in r.headers.items()}, (b"" if head else r.read())
    except urllib.error.HTTPError:
        raise
    except urllib.error.URLError as e:
        if not isinstance(e.reason, ssl.SSLError):
            raise
        return _curl(url, head, timeout, headers)
