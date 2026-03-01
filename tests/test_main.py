from fastapi import HTTPException
import pytest
from urllib import error

from main import LocalJudgeResult, UrlCheckRequest, judge_url_locally, url_check, verify_api_key


def test_url_check_text_no_url_found_returns_unknown() -> None:
    result = url_check(UrlCheckRequest(input_type="text", input="これはURLを含まない本文です"), _=None)
    assert result["status"] == "unknown"
    assert result["reason_codes"] == ["no_url_found"]
    assert result["candidate_urls"] == []


def test_url_check_text_selected_url_not_in_candidates_raises_parse_error() -> None:
    with pytest.raises(HTTPException) as exc:
        url_check(
            UrlCheckRequest(
                input_type="text",
                input="候補は https://example.com のみ",
                selected_url="https://not-in-list.example",
            ),
            _=None,
        )
    assert exc.value.status_code == 400
    assert exc.value.detail["reason_code"] == "parse_error"


def test_judge_url_locally_returns_suspected_when_safe_browsing_has_matches(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeResponse:
        def __enter__(self) -> "FakeResponse":
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def read(self) -> bytes:
            return b'{"matches":[{"threatType":"SOCIAL_ENGINEERING"}]}'

    def fake_urlopen(req, timeout=0):  # noqa: ANN001
        _ = req, timeout
        return FakeResponse()

    monkeypatch.setenv("GOOGLE_SAFE_BROWSING_API_KEY", "dummy-key")
    monkeypatch.setattr("main.request.urlopen", fake_urlopen)

    result = judge_url_locally("https://example.com")
    assert result.status == "suspected"
    assert result.reason_codes == ["safe_browsing_hit"]
    assert result.open_recommendation == "warn"


def test_judge_url_locally_returns_likely_safe_when_safe_browsing_has_no_matches(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeResponse:
        def __enter__(self) -> "FakeResponse":
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def read(self) -> bytes:
            return b"{}"

    def fake_urlopen(req, timeout=0):  # noqa: ANN001
        _ = req, timeout
        return FakeResponse()

    monkeypatch.setenv("GOOGLE_SAFE_BROWSING_API_KEY", "dummy-key")
    monkeypatch.setattr("main.request.urlopen", fake_urlopen)

    result = judge_url_locally("https://example.com")
    assert result.status == "likely_safe"
    assert result.reason_codes == ["safe_browsing_no_hit"]
    assert result.open_recommendation == "allow"


def test_judge_url_locally_returns_unknown_when_api_key_is_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GOOGLE_SAFE_BROWSING_API_KEY", raising=False)

    result = judge_url_locally("https://example.com")
    assert result.status == "unknown"
    assert result.reason_codes == ["safe_browsing_config_error"]
    assert result.open_recommendation == "warn"


def test_judge_url_locally_returns_unknown_when_safe_browsing_times_out(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_urlopen(req, timeout=0):  # noqa: ANN001
        _ = req, timeout
        raise TimeoutError()

    monkeypatch.setenv("GOOGLE_SAFE_BROWSING_API_KEY", "dummy-key")
    monkeypatch.setattr("main.request.urlopen", fake_urlopen)

    result = judge_url_locally("https://example.com")
    assert result.status == "unknown"
    assert result.reason_codes == ["safe_browsing_timeout"]
    assert result.open_recommendation == "warn"


def test_judge_url_locally_returns_unknown_when_safe_browsing_request_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_urlopen(req, timeout=0):  # noqa: ANN001
        _ = req, timeout
        raise error.URLError("network down")

    monkeypatch.setenv("GOOGLE_SAFE_BROWSING_API_KEY", "dummy-key")
    monkeypatch.setattr("main.request.urlopen", fake_urlopen)

    result = judge_url_locally("https://example.com")
    assert result.status == "unknown"
    assert result.reason_codes == ["safe_browsing_request_failed"]
    assert result.open_recommendation == "warn"


def test_judge_url_locally_returns_unknown_when_safe_browsing_response_is_invalid_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeResponse:
        def __enter__(self) -> "FakeResponse":
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def read(self) -> bytes:
            return b"{not-json"

    def fake_urlopen(req, timeout=0):  # noqa: ANN001
        _ = req, timeout
        return FakeResponse()

    monkeypatch.setenv("GOOGLE_SAFE_BROWSING_API_KEY", "dummy-key")
    monkeypatch.setattr("main.request.urlopen", fake_urlopen)

    result = judge_url_locally("https://example.com")
    assert result.status == "unknown"
    assert result.reason_codes == ["safe_browsing_parse_failed"]
    assert result.open_recommendation == "warn"


def test_verify_api_key_raises_401_when_authorization_header_is_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("URL_CHECKER_API_KEY", "dummy-secret")

    with pytest.raises(HTTPException) as exc:
        verify_api_key(None)
    assert exc.value.status_code == 401
    assert exc.value.detail["reason_code"] == "unauthorized"


def test_verify_api_key_raises_401_when_bearer_token_is_invalid(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("URL_CHECKER_API_KEY", "dummy-secret")

    with pytest.raises(HTTPException) as exc:
        verify_api_key("Bearer wrong-secret")
    assert exc.value.status_code == 401
    assert exc.value.detail["reason_code"] == "unauthorized"


def test_verify_api_key_accepts_valid_bearer_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("URL_CHECKER_API_KEY", "dummy-secret")

    verify_api_key("Bearer dummy-secret")


def test_verify_api_key_raises_500_when_server_key_is_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("URL_CHECKER_API_KEY", raising=False)

    with pytest.raises(HTTPException) as exc:
        verify_api_key("Bearer anything")
    assert exc.value.status_code == 500
    assert exc.value.detail["reason_code"] == "server_error"


def test_url_check_normalizes_url_input(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "main.judge_url_locally",
        lambda url: LocalJudgeResult(
            status="likely_safe",
            reason_codes=["stub"],
            message=f"stub for {url}",
            open_recommendation="allow",
        ),
    )

    result = url_check(UrlCheckRequest(input_type="url", input="  EXAMPLE.COM/path  "), _=None)
    assert result["normalized_url"] == "https://example.com/path"
    assert result["domain"] == "example.com"


def test_url_check_text_accepts_selected_url_when_only_host_case_differs(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "main.judge_url_locally",
        lambda url: LocalJudgeResult(
            status="likely_safe",
            reason_codes=["stub"],
            message=f"stub for {url}",
            open_recommendation="allow",
        ),
    )

    result = url_check(
        UrlCheckRequest(
            input_type="text",
            input="候補は https://example.com/path のみ",
            selected_url="https://EXAMPLE.com/path",
        ),
        _=None,
    )
    assert result["normalized_url"] == "https://example.com/path"


def test_url_check_text_returns_normalized_candidate_urls(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "main.judge_url_locally",
        lambda url: LocalJudgeResult(
            status="likely_safe",
            reason_codes=["stub"],
            message=f"stub for {url}",
            open_recommendation="allow",
        ),
    )

    result = url_check(
        UrlCheckRequest(input_type="text", input="候補 https://EXAMPLE.com/path"),
        _=None,
    )
    assert result["candidate_urls"] == ["https://example.com/path"]
