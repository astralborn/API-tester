"""Tests for managers/requests_manager.py — helpers and RequestManager."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def request_manager():
    """A RequestManager with LOGS_FOLDER patched to avoid touching the real log dir."""
    with patch("managers.requests_manager.LOGS_FOLDER") as mock_logs:
        mock_logs.mkdir = MagicMock()
        mock_logs.__truediv__ = lambda self, other: Path("/tmp") / other
        from managers.requests_manager import RequestManager
        yield RequestManager()


@pytest.fixture()
def make_worker(tmp_path):
    """Factory that builds a RequestWorker in isolation (no QThread.start, no HTTP)."""
    from managers.requests_manager import RequestWorker

    def _factory(preset_name="MyPreset", log_file=None):
        worker = RequestWorker.__new__(RequestWorker)
        worker.url = "http://1.2.3.4/api"
        worker.user = "admin"
        worker.password = bytearray(b"pass")
        worker.payload = {}
        worker.preset_name = preset_name
        worker.json_type = "normal"
        worker.log_file = log_file
        worker.logger = MagicMock()
        return worker

    return _factory


# ---------------------------------------------------------------------------
# make_safe_filename
# ---------------------------------------------------------------------------

class TestMakeSafeFilename:
    @pytest.fixture(autouse=True)
    def _import(self):
        from managers.requests_manager import make_safe_filename
        self.fn = make_safe_filename

    def test_replaces_spaces(self):
        assert " " not in self.fn("hello world")

    def test_replaces_slashes(self):
        result = self.fn("a/b\\c")
        assert "/" not in result
        assert "\\" not in result

    def test_keeps_alphanumeric_dot_dash(self):
        assert self.fn("abc-123.log") == "abc-123.log"

    def test_caps_at_64_chars(self):
        assert len(self.fn("a" * 100)) <= 64

    def test_empty_string(self):
        assert self.fn("") == ""

    def test_all_special_chars(self):
        assert all(c == "_" for c in self.fn("!@#$%^&*()"))


# ---------------------------------------------------------------------------
# RequestManager.build_request
# ---------------------------------------------------------------------------

class TestBuildRequest:
    def test_url_built_correctly(self, request_manager):
        url, _ = request_manager.build_request("10.0.0.1", "/api/call", None, False)
        assert url == "http://10.0.0.1/api/call"

    def test_simple_format_appends_query(self, request_manager):
        url, _ = request_manager.build_request("10.0.0.1", "/api/call", None, True)
        assert "format=simple" in url

    def test_simple_format_uses_ampersand_when_query_exists(self, request_manager):
        url, _ = request_manager.build_request("10.0.0.1", "/api?foo=bar", None, True)
        assert url.count("?") == 1
        assert "format=simple" in url

    def test_no_json_file_gives_empty_payload(self, request_manager):
        _, payload = request_manager.build_request("10.0.0.1", "/api/call", None, False)
        assert payload == {}

    def test_none_json_file_gives_empty_payload(self, request_manager):
        _, payload = request_manager.build_request("10.0.0.1", "/api/call", "(none)", False)
        assert payload == {}

    def test_loads_payload_from_json_file(self, request_manager, tmp_path):
        json_file = tmp_path / "test.json"
        json_file.write_text('{"method": "GetContacts"}', encoding="utf-8")
        with patch("managers.requests_manager.JSON_FOLDER", tmp_path):
            _, payload = request_manager.build_request("10.0.0.1", "/api/call", "test.json", False)
        assert payload == {"method": "GetContacts"}

    def test_missing_json_file_gives_empty_payload(self, request_manager, tmp_path):
        with patch("managers.requests_manager.JSON_FOLDER", tmp_path):
            _, payload = request_manager.build_request("10.0.0.1", "/api/call", "ghost.json", False)
        assert payload == {}


# ---------------------------------------------------------------------------
# RequestManager.start_new_log
# ---------------------------------------------------------------------------

class TestStartNewLog:
    def test_returns_path_object(self, request_manager):
        assert isinstance(request_manager.start_new_log("MyPreset"), Path)

    def test_filename_contains_preset_name(self, request_manager):
        assert "GetContacts" in request_manager.start_new_log("GetContacts").name

    def test_unsafe_chars_sanitised(self, request_manager):
        result = request_manager.start_new_log("Get Contacts/Test")
        assert "/" not in result.name
        assert " " not in result.name


# ---------------------------------------------------------------------------
# RequestWorker._write_log / _ensure_log_file
# ---------------------------------------------------------------------------

class TestRequestWorkerWriteLog:
    def test_write_log_creates_file(self, make_worker, tmp_path):
        log = tmp_path / "test.log"
        worker = make_worker(log_file=log)
        worker._write_log("some response text", "ok")
        assert log.exists()

    def test_write_log_appends_tag(self, make_worker, tmp_path):
        log = tmp_path / "test.log"
        worker = make_worker(log_file=log)
        worker._write_log("body", "warn")
        content = log.read_text(encoding="utf-8")
        assert "warn" in content
        assert "body" in content

    def test_write_log_multipreset_adds_header(self, make_worker, tmp_path):
        # A log file whose name contains "MultiPreset_Run" triggers a preset header line
        log = tmp_path / "log_MultiPreset_Run_20260101.log"
        worker = make_worker(log_file=log)
        worker._write_log("body", "ok")
        assert "MyPreset" in log.read_text(encoding="utf-8")

    def test_ensure_log_file_sets_path_when_none(self, make_worker, tmp_path):
        worker = make_worker(log_file=None)
        with patch("managers.requests_manager.LOGS_FOLDER", tmp_path):
            worker._ensure_log_file()
        assert worker.log_file is not None
        assert "MyPreset" in worker.log_file.name


# ---------------------------------------------------------------------------
# RequestWorker.run — success and error paths (no real HTTP)
# ---------------------------------------------------------------------------

class TestRequestWorkerRun:
    """Test RequestWorker.run() by patching requests.post so no real network call happens.

    run() calls self.finished.emit() at the end. Because we bypass QThread.__init__
    via __new__, 'finished' is still the class-level Signal descriptor — we replace
    it with a MagicMock on the instance so emit() can be inspected without a live
    Qt event loop.
    """

    @pytest.fixture()
    def worker(self, make_worker, tmp_path):
        w = make_worker(preset_name="RunTest", log_file=tmp_path / "run.log")
        w.password = bytearray(b"secret")
        w.payload = {"key": "val"}
        w.finished = MagicMock()
        return w

    def test_run_success_emits_ok_tag(self, worker):
        """Successful 200 response → tag 'ok' emitted, password zeroed."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = '{"result":"ok"}'
        mock_resp.elapsed.total_seconds.return_value = 0.05

        with patch("managers.requests_manager.requests.post", return_value=mock_resp):
            worker.run()

        _, preset_name, tag = worker.finished.emit.call_args[0]
        assert tag == "ok"
        assert preset_name == "RunTest"
        assert all(b == 0 for b in worker.password)

    def test_run_non_200_emits_warn_tag(self, worker):
        """Non-200 status → tag 'warn'."""
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_resp.text = "Not Found"
        mock_resp.elapsed.total_seconds.return_value = 0.1

        with patch("managers.requests_manager.requests.post", return_value=mock_resp):
            worker.run()

        _, _, tag = worker.finished.emit.call_args[0]
        assert tag == "warn"

    def test_run_network_error_emits_err_tag(self, worker):
        """Network exception → tag 'err', password zeroed."""
        import requests as req_lib

        with patch("managers.requests_manager.requests.post",
                   side_effect=req_lib.exceptions.ConnectionError("refused")):
            worker.run()

        _, _, tag = worker.finished.emit.call_args[0]
        assert tag == "err"
        assert all(b == 0 for b in worker.password)

    def test_run_writes_log_file(self, worker, tmp_path):
        """run() must write the response to the log file."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = "response body"
        mock_resp.elapsed.total_seconds.return_value = 0.0

        with patch("managers.requests_manager.requests.post", return_value=mock_resp):
            worker.run()

        assert worker.log_file.exists()
        assert "response body" in worker.log_file.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# RequestManager._remove_worker / send_request_async
# ---------------------------------------------------------------------------

class TestRequestManagerWorkerTracking:
    def test_remove_worker_removes_existing(self, request_manager):
        w = MagicMock()
        request_manager.workers = [w]
        request_manager._remove_worker(w)
        assert w not in request_manager.workers

    def test_remove_worker_is_noop_for_unknown(self, request_manager):
        request_manager.workers = []
        request_manager._remove_worker(MagicMock())  # must not raise

    def test_send_request_async_starts_worker_and_returns_it(self, request_manager, tmp_path):
        """send_request_async must build a worker, start it, and return it."""
        fake_worker = MagicMock()
        with (
            patch("managers.requests_manager.RequestWorker", return_value=fake_worker),
            patch("managers.requests_manager.JSON_FOLDER", tmp_path),
        ):
            result = request_manager.send_request_async(
                ip="10.0.0.1",
                user="admin",
                password=bytearray(b"pw"),
                endpoint="/api/test",
                json_file=None,
                simple_format=False,
                json_type="normal",
                callback=MagicMock(),
            )

        fake_worker.start.assert_called_once()
        assert result is fake_worker


# ---------------------------------------------------------------------------
# RequestWorker.__init__ (real constructor — lines 50-58)
# ---------------------------------------------------------------------------

class TestRequestWorkerInit:
    def test_init_sets_all_attributes(self, qapp):
        """Real __init__ runs via super().__init__() which needs a QApplication."""
        from managers.requests_manager import RequestWorker
        worker = RequestWorker(
            url="http://1.2.3.4/api",
            user="admin",
            password=bytearray(b"pass"),
            payload={"k": "v"},
            preset_name="MyPreset",
            json_type="google",
        )
        assert worker.url == "http://1.2.3.4/api"
        assert worker.user == "admin"
        assert worker.payload == {"k": "v"}
        assert worker.preset_name == "MyPreset"
        assert worker.json_type == "google"
        assert worker.log_file is None


# ---------------------------------------------------------------------------
# RequestWorker._write_log edge cases (lines 125, 132-133)
# ---------------------------------------------------------------------------

class TestWriteLogEdgeCases:
    def test_write_log_with_none_log_file_is_noop(self, make_worker):
        # log_file is None → early return, nothing written (line 125)
        worker = make_worker(log_file=None)
        worker._write_log("body", "ok")  # must not raise and must not create any file

    def test_write_log_handles_io_error_silently(self, make_worker, tmp_path):
        # Exception during file write → logged silently, must not propagate (lines 132-133)
        log = tmp_path / "unwritable.log"
        worker = make_worker(log_file=log)
        with patch.object(Path, "open", side_effect=OSError("permission denied")):
            worker._write_log("body", "ok")  # must not raise
        worker.logger.error.assert_called_once()


