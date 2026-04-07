from fastapi import APIRouter, HTTPException
from database import supabase
from models import ListCreate, ListUpdate

router = APIRouter(prefix="/boards/{board_id}/lists", tags=["lists"])


@router.get("/")
def get_lists(board_id: str):
    """보드의 리스트(컬럼) 조회"""
    res = (
        supabase.table("lists")
        .select("*, cards(id, title, position, due_date, priority_score)")
        .eq("board_id", board_id)
        .order("position")
        .execute()
    )
    return res.data


@router.post("/", status_code=201)
def create_list(board_id: str, lst: ListCreate):
    """리스트(컬럼) 생성"""
    payload = lst.model_dump()
    payload["board_id"] = board_id
    res = supabase.table("lists").insert(payload).execute()
    if not res.data:
        raise HTTPException(status_code=400, detail="리스트 생성 실패")
    return res.data[0]


@router.patch("/{list_id}")
def update_list(board_id: str, list_id: str, lst: ListUpdate):
    """리스트 수정"""
    data = {k: v for k, v in lst.model_dump().items() if v is not None}
    res = supabase.table("lists").update(data).eq("id", list_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="리스트를 찾을 수 없습니다")
    return res.data[0]


@router.delete("/{list_id}", status_code=204)
def delete_list(board_id: str, list_id: str):
    """리스트 삭제"""
    supabase.table("lists").delete().eq("id", list_id).execute()
