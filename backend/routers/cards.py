from fastapi import APIRouter, HTTPException
from database import supabase
from models import CardCreate, CardUpdate, CardMove, CommentCreate

router = APIRouter(tags=["cards"])


# ── Cards in a List ────────────────────────────────────────────────────────────

@router.get("/lists/{list_id}/cards")
def get_cards(list_id: str):
    """리스트의 카드 조회"""
    res = (
        supabase.table("cards")
        .select("*, card_members(user_id), card_labels(label_id)")
        .eq("list_id", list_id)
        .order("position")
        .execute()
    )
    return res.data


@router.post("/lists/{list_id}/cards", status_code=201)
def create_card(list_id: str, card: CardCreate):
    """카드 생성"""
    payload = card.model_dump()
    payload["list_id"] = list_id
    if payload.get("due_date"):
        payload["due_date"] = payload["due_date"].isoformat()
    res = supabase.table("cards").insert(payload).execute()
    if not res.data:
        raise HTTPException(status_code=400, detail="카드 생성 실패")
    return res.data[0]


# ── Single Card ────────────────────────────────────────────────────────────────

@router.get("/cards/{card_id}")
def get_card(card_id: str):
    """카드 상세 조회"""
    res = (
        supabase.table("cards")
        .select("*, card_members(user_id), card_labels(labels(*)), comments(*)")
        .eq("id", card_id)
        .single()
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=404, detail="카드를 찾을 수 없습니다")
    return res.data


@router.patch("/cards/{card_id}")
def update_card(card_id: str, card: CardUpdate):
    """카드 수정"""
    data = {k: v for k, v in card.model_dump().items() if v is not None}
    if "due_date" in data and data["due_date"]:
        data["due_date"] = data["due_date"].isoformat()
    data["updated_at"] = "now()"
    res = supabase.table("cards").update(data).eq("id", card_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="카드를 찾을 수 없습니다")
    return res.data[0]


@router.patch("/cards/{card_id}/move")
def move_card(card_id: str, move: CardMove):
    """카드를 다른 리스트로 이동"""
    res = supabase.table("cards").update(
        {"list_id": move.list_id, "position": move.position, "updated_at": "now()"}
    ).eq("id", card_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="카드를 찾을 수 없습니다")
    return res.data[0]


@router.delete("/cards/{card_id}", status_code=204)
def delete_card(card_id: str):
    """카드 삭제"""
    supabase.table("cards").delete().eq("id", card_id).execute()


# ── Comments ───────────────────────────────────────────────────────────────────

@router.get("/cards/{card_id}/comments")
def get_comments(card_id: str):
    """카드 댓글 조회"""
    res = (
        supabase.table("comments")
        .select("*, profiles(name, avatar_url)")
        .eq("card_id", card_id)
        .order("created_at")
        .execute()
    )
    return res.data


@router.post("/cards/{card_id}/comments", status_code=201)
def add_comment(card_id: str, comment: CommentCreate):
    """댓글 추가"""
    payload = comment.model_dump()
    payload["card_id"] = card_id
    res = supabase.table("comments").insert(payload).execute()
    if not res.data:
        raise HTTPException(status_code=400, detail="댓글 생성 실패")
    return res.data[0]


# ── Card Members & Labels ──────────────────────────────────────────────────────

@router.post("/cards/{card_id}/members")
def assign_member(card_id: str, user_id: str):
    """카드에 멤버 배정"""
    res = supabase.table("card_members").insert(
        {"card_id": card_id, "user_id": user_id}
    ).execute()
    return res.data[0] if res.data else {}


@router.delete("/cards/{card_id}/members/{user_id}", status_code=204)
def remove_member(card_id: str, user_id: str):
    """카드 멤버 제거"""
    supabase.table("card_members").delete().eq("card_id", card_id).eq("user_id", user_id).execute()


@router.post("/cards/{card_id}/labels")
def add_label(card_id: str, label_id: str):
    """카드에 라벨 추가"""
    res = supabase.table("card_labels").insert(
        {"card_id": card_id, "label_id": label_id}
    ).execute()
    return res.data[0] if res.data else {}
