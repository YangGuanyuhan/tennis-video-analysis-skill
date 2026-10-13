"""Local static preview with byte ranges for large source videos."""
from __future__ import annotations

import re
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


class RangeHandler(SimpleHTTPRequestHandler):
    def send_head(self):
        target = Path(self.translate_path(self.path)).resolve()
        root = Path(self.directory).resolve()
        if not target.is_relative_to(root):
            self.send_error(403)
            return None
        self.remaining = None
        raw = self.headers.get("Range")
        if not raw or not target.is_file():
            return super().send_head()
        size = target.stat().st_size
        match = re.fullmatch(r"bytes=(\d*)-(\d*)", raw.strip())
        if not match or not any(match.groups()) or not size:
            self.send_response(416)
            self.send_header("Content-Range", f"bytes */{size}")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return None
        if match[1]:
            start, end = int(match[1]), int(match[2]) if match[2] else size - 1
        else:
            start, end = max(0, size - int(match[2])), size - 1
        if start >= size or end < start:
            self.send_response(416)
            self.send_header("Content-Range", f"bytes */{size}")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return None
        end = min(end, size - 1)
        source = target.open("rb")
        source.seek(start)
        self.remaining = end - start + 1
        self.send_response(206)
        self.send_header("Content-Type", self.guess_type(str(target)))
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.send_header("Content-Length", str(self.remaining))
        self.end_headers()
        return source

    def copyfile(self, source, outputfile):
        try:
            if self.remaining is None:
                return super().copyfile(source, outputfile)
            remaining = self.remaining
            while remaining:
                chunk = source.read(min(262144, remaining))
                if not chunk:
                    break
                outputfile.write(chunk)
                remaining -= len(chunk)
        except (ConnectionResetError, BrokenPipeError):
            pass

    def log_message(self, *args):
        pass


def serve(directory: Path, port: int = 8765):
    root = Path(directory).resolve(strict=True)
    if not root.is_dir():
        raise ValueError("Serve a directory")
    server = ThreadingHTTPServer(("127.0.0.1", port), partial(RangeHandler, directory=str(root)))
    print(f"http://127.0.0.1:{server.server_port}/  (Ctrl+C to stop)", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
