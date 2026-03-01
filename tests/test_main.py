from fastapi import HTTPException
import pytest

from main import UrlCheckRequest, url_check


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
