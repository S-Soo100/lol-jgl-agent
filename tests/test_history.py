"""누적 히스토리 병합 + 계정 분리 테스트."""
import lol_jgl_agent.config as config
import lol_jgl_agent.history as history


def test_account_separation(tmp_path, monkeypatch):
    """본캐/부캐 히스토리가 절대 섞이지 않아야 한다."""
    monkeypatch.setattr(history, "HISTORY_PATH", tmp_path / "history.json")
    monkeypatch.setattr(history, "REPORTS_DIR", tmp_path)

    class _S:
        default_riot_id = "메인#KR1"

        @staticmethod
        def load():
            return _S()

    monkeypatch.setattr(config, "Settings", _S)

    # 기본 계정(생략/일치) → history.json
    assert history.history_path(None) == tmp_path / "history.json"
    assert history.history_path("메인#KR1") == tmp_path / "history.json"
    # 부캐 → 별도 파일
    assert history.history_path("꽃게잡이#게잡이") == tmp_path / "history_꽃게잡이-게잡이.json"

    history.merge([{"match_id": "KR_1"}])                     # 본캐
    history.merge([{"match_id": "KR_9"}], "꽃게잡이#게잡이")    # 부캐

    assert [g["match_id"] for g in history.load_history()] == ["KR_1"]
    assert [g["match_id"] for g in history.load_history("꽃게잡이#게잡이")] == ["KR_9"]


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
