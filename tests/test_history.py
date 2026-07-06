"""누적 히스토리 병합 테스트."""
import lol_jgl_agent.history as history


def test_merge_dedup_and_sort(tmp_path, monkeypatch):
    monkeypatch.setattr(history, "HISTORY_PATH", tmp_path / "history.json")

    added, total, ids = history.merge([{"match_id": "KR_2"}, {"match_id": "KR_1"}])
    assert (added, total) == (2, 2)

    # 하나 중복(KR_2) + 하나 신규(KR_3)
    added, total, ids = history.merge([{"match_id": "KR_2"}, {"match_id": "KR_3"}])
    assert added == 1
    assert total == 3
    assert ids == ["KR_3"]

    # 내림차순 정렬 유지
    assert [g["match_id"] for g in history.load_history()] == ["KR_3", "KR_2", "KR_1"]
