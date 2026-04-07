from fastapi import APIRouter, HTTPException
from database import supabase
from models import BoardCreate, BoardUpdate

router = APIRouter(prefix="/boards", tags=["boards"])


@router.get("/")
def list_boards():
    """모든 보드 조회"""
    res = supabase.table("boards").select("*, profiles(name, email)").execute()
    return res.data


@router.post("/", status_code=201)
def create_board(board: BoardCreate):
    """새 보드 생성"""
    res = supabase.table("boards").insert(board.model_dump()).execute()
    if not res.data:
        raise HTTPException(status_code=400, detail="보드 생성 실패")
    return res.data[0]


@router.get("/{board_id}")
def get_board(board_id: str):
    """보드 상세 조회 (리스트 + 카드 포함)"""
    res = (
        supabase.table("boards")
        .select("*, lists(*, cards(*, card_members(user_id), card_labels(label_id)))")
        .eq("id", board_id)
        .single()
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=404, detail="보드를 찾을 수 없습니다")
    return res.data


@router.patch("/{board_id}")
def update_board(board_id: str, board: BoardUpdate):
    """보드 수정"""
    data = {k: v for k, v in board.model_dump().items() if v is not None}
    res = supabase.table("boards").update(data).eq("id", board_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="보드를 찾을 수 없습니다")
    return res.data[0]


@router.delete("/{board_id}", status_code=204)
def delete_board(board_id: str):
    """보드 삭제"""
    supabase.table("boards").delete().eq("id", board_id).execute()


@router.get("/{board_id}/members")
def get_board_members(board_id: str):
    """보드 멤버 조회"""
    res = (
        supabase.table("board_members")
        .select("*, profiles(name, email, avatar_url)")
        .eq("board_id", board_id)
        .execute()
    )
    return res.data


@router.post("/{board_id}/members")
def add_board_member(board_id: str, user_id: str, role: str = "member"):
    """보드에 멤버 추가"""
    res = supabase.table("board_members").insert(
        {"board_id": board_id, "user_id": user_id, "role": role}
    ).execute()
    if not res.data:
        raise HTTPException(status_code=400, detail="멤버 추가 실패")
    return res.data[0]
