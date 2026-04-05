import json
import logging

from app import observability


def test_json_formatter_includes_message_and_extra_fields() -> None:
    formatter = observability.JsonFormatter()
    record = logging.LogRecord(
        name="test.logger",
        level=logging.INFO,
        pathname=__file__,
        lineno=12,
        msg="hello %s",
        args=("world",),
        exc_info=None,
    )
    record.component = "observability"

    payload = json.loads(formatter.format(record))

    assert payload["level"] == "INFO"
    assert payload["logger"] == "test.logger"
    assert payload["message"] == "hello world"
    assert payload["component"] == "observability"


def test_read_recent_logs_returns_json_and_raw_lines(tmp_path) -> None:
    log_file = tmp_path / "app.log"
    log_file.write_text('{"event":"ok"}\nnot-json\n', encoding="utf-8")

    records = observability.read_recent_logs(str(log_file))

    assert records == [{"event": "ok"}, {"raw": "not-json"}]


def test_get_system_metrics_returns_expected_shape() -> None:
    metrics = observability.get_system_metrics()

    assert "timestamp" in metrics
    assert "cpu" in metrics
    assert "memory" in metrics
    assert "process" in metrics
    assert "percent" in metrics["cpu"]
    assert "rss_bytes" in metrics["process"]


def test_setup_logging_creates_log_file_and_handlers(tmp_path, monkeypatch) -> None:
    log_file = tmp_path / "logs" / "app.log"
    monkeypatch.setenv("LOG_FILE", str(log_file))
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("LOG_MAX_BYTES", "1024")
    monkeypatch.setenv("LOG_BACKUP_COUNT", "1")

    configured_log_file = observability.setup_logging()
    logging.getLogger().info("test log line", extra={"component": "test"})

    assert configured_log_file == str(log_file)
    assert log_file.exists()
    contents = log_file.read_text(encoding="utf-8")
    assert "Logging configured" in contents
    assert "test log line" in contents
