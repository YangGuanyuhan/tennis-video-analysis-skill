import threading
from functools import partial
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from tennis_analysis.server import RangeHandler


@pytest.fixture
def local_server(tmp_path):
    (tmp_path / "video.bin").write_bytes(bytes(range(100)))
    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(RangeHandler, directory=str(tmp_path)))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}/video.bin"
    server.shutdown()
    server.server_close()
    thread.join(timeout=3)


@pytest.mark.parametrize("header,expected", [("bytes=10-19", bytes(range(10, 20))), ("bytes=-5", bytes(range(95, 100))), ("bytes=97-", bytes(range(97, 100)))])
def test_byte_ranges_for_large_video_seeking(local_server, header, expected):
    with urlopen(Request(local_server, headers={"Range": header}), timeout=3) as response:
        assert response.status == 206
        assert response.read() == expected
        assert response.headers["Accept-Ranges"] == "bytes"


def test_invalid_range_is_not_silently_treated_as_full_video(local_server):
    with pytest.raises(HTTPError) as error:
        urlopen(Request(local_server, headers={"Range": "bytes=500-600"}), timeout=3)
    assert error.value.code == 416
