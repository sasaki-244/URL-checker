from fastapi import HTTPException
import pytest

from main import UrlCheckRequest, judge_url_locally, url_check


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
    assert result.reason_codes == ["no_hit"]
    assert result.open_recommendation == "allow"
