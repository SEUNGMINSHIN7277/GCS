"""
Supabase를 Mock으로 대체한 통합 테스트
실제 DB 연결 없이 전체 API 흐름을 검증합니다.
"""
import uuid
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient


# ── Mock Supabase 데이터 ───────────────────────────────────────────────────────
BOARD_ID   = str(uuid.uuid4())
LIST_ID    = str(uuid.uuid4())
CARD_ID    = str(uuid.uuid4())
OWNER_ID   = str(uuid.uuid4())
USER_ID    = str(uuid.uuid4())

MOCK_BOARD = {
    "id": BOARD_ID, "title": "과제5 칸반",
    "description": "팀 공유 보드", "owner_id": OWNER_ID,
    "created_at": "2026-04-07T00:00:00+00:00",
    "lists": [],
}
MOCK_LIST = {
    "id": LIST_ID, "board_id": BOARD_ID, "title": "In Progress",
    "position": 1.0, "wip_limit": 3,
    "created_at": "2026-04-07T00:00:00+00:00",
}
MOCK_CARD = {
    "id": CARD_ID, "list_id": LIST_ID,
    "title": "FastAPI 백엔드 구현",
    "description": "Supabase 연동 REST API",
    "position": 0.0, "priority_score": 0.0,
    "due_date": "2026-04-10T00:00:00+00:00",
    "created_at": "2026-04-07T00:00:00+00:00",
    "updated_at": "2026-04-07T00:00:00+00:00",
    "card_members": [], "card_labels": [], "task_insights": [], "comments": [],
}


def make_mock_supabase():
    """Supabase 클라이언트를 흉내내는 Mock 객체 생성"""
    mock = MagicMock()

    def table(name):
        t = MagicMock()
        # 체이닝 메서드들
        for method in ("select", "insert", "update", "delete", "eq",
                       "order", "single", "limit"):
            getattr(t, method).return_value = t

        if name == "boards":
            t.execute.return_value = MagicMock(data=[MOCK_BOARD])
        elif name == "lists":
            t.execute.return_value = MagicMock(data=[MOCK_LIST])
        elif name == "cards":
            t.execute.return_value = MagicMock(data=[MOCK_CARD])
        elif name == "comments":
            t.execute.return_value = MagicMock(data=[{
                "id": str(uuid.uuid4()), "card_id": CARD_ID,
                "user_id": USER_ID, "content": "작업 시작합니다",
                "created_at": "2026-04-07T00:00:00+00:00",
                "profiles": {"name": "홍길동", "avatar_url": None},
            }])
        elif name == "board_members":
            t.execute.return_value = MagicMock(data=[{
                "board_id": BOARD_ID, "user_id": OWNER_ID, "role": "owner",
            }])
        else:
            t.execute.return_value = MagicMock(data=[])
        return t

    mock.table.side_effect = table
    return mock


# ── 테스트 실행 ────────────────────────────────────────────────────────────────
def run_tests():
    with patch("database._client", make_mock_supabase()):
        from main import app
        client = TestClient(app)
        results = []

        def test(name, method, url, expected_status, json=None):
            if json is not None:
                r = getattr(client, method)(url, json=json)
            else:
                r = getattr(client, method)(url)
            ok = r.status_code == expected_status
            results.append((name, ok, r.status_code, r.json() if ok else r.text[:80]))
            return r

        print("\n" + "="*60)
        print("  칸반 보드 API 통합 테스트 (Mock)")
        print("="*60)

        # 기본 엔드포인트
        test("GET /              (서버 상태)",      "get", "/",       200)
        test("GET /health        (헬스체크)",        "get", "/health", 200)

        # 보드 CRUD
        test("GET  /boards/      (보드 목록)",       "get",  "/boards/",    200)
        test("POST /boards/      (보드 생성)",       "post", "/boards/",    201,
             json={"title": "과제5 칸반", "owner_id": OWNER_ID})
        test(f"GET  /boards/{{id}} (보드 상세)",     "get",  f"/boards/{BOARD_ID}", 200)
        test(f"PATCH /boards/{{id}} (보드 수정)",    "patch",f"/boards/{BOARD_ID}", 200,
             json={"title": "과제5 칸반 (수정)"})
        test(f"GET  /boards/{{id}}/members",         "get",  f"/boards/{BOARD_ID}/members", 200)

        # 리스트 CRUD
        test(f"GET  /boards/{{id}}/lists/",          "get",  f"/boards/{BOARD_ID}/lists/", 200)
        test(f"POST /boards/{{id}}/lists/",          "post", f"/boards/{BOARD_ID}/lists/", 201,
             json={"title": "In Progress", "position": 1.0, "wip_limit": 3})
        test(f"PATCH .../lists/{{id}} (리스트 수정)","patch",f"/boards/{BOARD_ID}/lists/{LIST_ID}", 200,
             json={"title": "진행 중"})

        # 카드 CRUD
        test(f"GET  /lists/{{id}}/cards",            "get",  f"/lists/{LIST_ID}/cards", 200)
        test(f"POST /lists/{{id}}/cards (카드 생성)","post", f"/lists/{LIST_ID}/cards", 201,
             json={"title": "FastAPI 백엔드 구현", "due_date": "2026-04-10T00:00:00+00:00"})
        test(f"GET  /cards/{{id}} (카드 상세)",       "get",  f"/cards/{CARD_ID}", 200)
        test(f"PATCH /cards/{{id}} (카드 수정)",      "patch",f"/cards/{CARD_ID}", 200,
             json={"title": "FastAPI 백엔드 구현 (완료)"})
        test(f"PATCH /cards/{{id}}/move (카드 이동)","patch",f"/cards/{CARD_ID}/move", 200,
             json={"list_id": LIST_ID, "position": 1.0})

        # 댓글
        test(f"GET  /cards/{{id}}/comments",         "get",  f"/cards/{CARD_ID}/comments", 200)
        test(f"POST /cards/{{id}}/comments",         "post", f"/cards/{CARD_ID}/comments", 201,
             json={"user_id": USER_ID, "content": "작업 시작합니다"})

        # 결과 출력
        print()
        passed = sum(1 for _, ok, *_ in results if ok)
        total  = len(results)

        for name, ok, status, data in results:
            icon = "✅" if ok else "❌"
            print(f"  {icon} {name:45s}  [{status}]")

        print()
        print(f"  결과: {passed}/{total} 통과")
        print("="*60 + "\n")
        return passed == total


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)
