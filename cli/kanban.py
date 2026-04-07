#!/usr/bin/env python3
"""칸반 보드 CLI - FastAPI 백엔드와 연동"""

import os
import sys
import click
import requests
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich import box

load_dotenv()

API_URL = os.getenv("KANBAN_API_URL", "http://localhost:8000")
console = Console()


def api(method: str, path: str, **kwargs):
    """공통 API 호출 헬퍼"""
    url = f"{API_URL}{path}"
    try:
        res = requests.request(method, url, **kwargs)
        res.raise_for_status()
        return res.json() if res.content else None
    except requests.exceptions.ConnectionError:
        console.print(f"[red]오류:[/red] API 서버에 연결할 수 없습니다 ({API_URL})")
        sys.exit(1)
    except requests.exceptions.HTTPError as e:
        console.print(f"[red]오류:[/red] {e.response.status_code} - {e.response.text}")
        sys.exit(1)


# ── CLI 그룹 ──────────────────────────────────────────────────────────────────

@click.group()
def cli():
    """칸반 보드 CLI - 팀 공유 칸반 보드를 터미널에서 관리합니다"""
    pass


# ── 보드 명령어 ────────────────────────────────────────────────────────────────

@cli.group()
def board():
    """보드 관련 명령어"""
    pass


@board.command("list")
def board_list():
    """모든 보드 목록 조회"""
    boards = api("GET", "/boards/")
    if not boards:
        console.print("[yellow]보드가 없습니다.[/yellow]")
        return

    table = Table(title="칸반 보드 목록", box=box.ROUNDED)
    table.add_column("ID", style="dim", max_width=8)
    table.add_column("제목", style="bold cyan")
    table.add_column("설명")
    table.add_column("생성일")

    for b in boards:
        table.add_row(
            b["id"][:8],
            b["title"],
            b.get("description") or "-",
            b.get("created_at", "")[:10],
        )
    console.print(table)


@board.command("create")
@click.argument("title")
@click.option("--desc", "-d", default=None, help="보드 설명")
@click.option("--owner", "-o", required=True, help="소유자 user_id (UUID)")
def board_create(title, desc, owner):
    """새 보드 생성"""
    result = api("POST", "/boards/", json={"title": title, "description": desc, "owner_id": owner})
    console.print(f"[green]✓[/green] 보드 생성됨: [bold]{result['title']}[/bold] (ID: {result['id'][:8]})")


@board.command("show")
@click.argument("board_id")
def board_show(board_id):
    """보드 상세 보기 (리스트 + 카드)"""
    b = api("GET", f"/boards/{board_id}")

    console.print(f"\n[bold cyan]📋 {b['title']}[/bold cyan]")
    if b.get("description"):
        console.print(f"   {b['description']}\n")

    lists = sorted(b.get("lists", []), key=lambda x: x.get("position", 0))
    for lst in lists:
        cards = sorted(lst.get("cards", []), key=lambda x: x.get("position", 0))
        wip = f" (WIP: {lst['wip_limit']})" if lst.get("wip_limit") else ""
        console.print(f"[bold yellow]── {lst['title']}{wip} ──[/bold yellow] (ID: {lst['id'][:8]})")
        if not cards:
            console.print("   [dim](카드 없음)[/dim]")
        for c in cards:
            due = f" [red]⏰ {c['due_date'][:10]}[/red]" if c.get("due_date") else ""
            console.print(f"   • [white]{c['title']}[/white]{due}  [dim]{c['id'][:8]}[/dim]")
        console.print()


# ── 리스트 명령어 ──────────────────────────────────────────────────────────────

@cli.group("list")
def list_cmd():
    """리스트(컬럼) 관련 명령어"""
    pass


@list_cmd.command("add")
@click.argument("board_id")
@click.argument("title")
@click.option("--position", "-p", default=0.0, help="컬럼 위치")
@click.option("--wip", default=0, help="WIP 제한 (0=무제한)")
def list_add(board_id, title, position, wip):
    """보드에 리스트(컬럼) 추가"""
    result = api("POST", f"/boards/{board_id}/lists",
                 json={"title": title, "position": position, "wip_limit": wip})
    console.print(f"[green]✓[/green] 리스트 생성됨: [bold]{result['title']}[/bold] (ID: {result['id'][:8]})")


@list_cmd.command("rename")
@click.argument("board_id")
@click.argument("list_id")
@click.argument("new_title")
def list_rename(board_id, list_id, new_title):
    """리스트 이름 변경"""
    result = api("PATCH", f"/boards/{board_id}/lists/{list_id}", json={"title": new_title})
    console.print(f"[green]✓[/green] 리스트 이름 변경됨: [bold]{result['title']}[/bold]")


# ── 카드 명령어 ────────────────────────────────────────────────────────────────

@cli.group("card")
def card_cmd():
    """카드(태스크) 관련 명령어"""
    pass


@card_cmd.command("list")
@click.argument("list_id")
def card_list(list_id):
    """리스트의 카드 목록 조회"""
    cards = api("GET", f"/lists/{list_id}/cards")
    if not cards:
        console.print("[yellow]카드가 없습니다.[/yellow]")
        return

    table = Table(box=box.SIMPLE)
    table.add_column("ID", style="dim", max_width=8)
    table.add_column("제목", style="bold")
    table.add_column("마감일")
    table.add_column("우선순위")

    for c in cards:
        table.add_row(
            c["id"][:8],
            c["title"],
            c.get("due_date", "-")[:10] if c.get("due_date") else "-",
            f"{c.get('priority_score', 0):.1f}",
        )
    console.print(table)


@card_cmd.command("add")
@click.argument("list_id")
@click.argument("title")
@click.option("--desc", "-d", default=None, help="카드 설명")
@click.option("--due", default=None, help="마감일 (YYYY-MM-DD)")
@click.option("--position", "-p", default=0.0, help="카드 위치")
def card_add(list_id, title, desc, due, position):
    """카드(태스크) 생성"""
    payload = {"title": title, "description": desc, "position": position}
    if due:
        payload["due_date"] = f"{due}T00:00:00+00:00"
    result = api("POST", f"/lists/{list_id}/cards", json=payload)
    console.print(f"[green]✓[/green] 카드 생성됨: [bold]{result['title']}[/bold] (ID: {result['id'][:8]})")


@card_cmd.command("show")
@click.argument("card_id")
def card_show(card_id):
    """카드 상세 조회"""
    c = api("GET", f"/cards/{card_id}")
    console.print(f"\n[bold cyan]🃏 {c['title']}[/bold cyan]  [dim]{c['id']}[/dim]")
    if c.get("description"):
        console.print(f"   {c['description']}")
    if c.get("due_date"):
        console.print(f"   마감일: [red]{c['due_date'][:10]}[/red]")
    comments = c.get("comments", [])
    if comments:
        console.print(f"\n[bold]댓글 ({len(comments)}개):[/bold]")
        for cm in comments:
            console.print(f"   • {cm['content']}  [dim]{cm['created_at'][:10]}[/dim]")


@card_cmd.command("update")
@click.argument("card_id")
@click.option("--title", "-t", default=None, help="새 제목")
@click.option("--desc", "-d", default=None, help="새 설명")
@click.option("--due", default=None, help="새 마감일 (YYYY-MM-DD)")
def card_update(card_id, title, desc, due):
    """카드 수정"""
    payload = {}
    if title:
        payload["title"] = title
    if desc:
        payload["description"] = desc
    if due:
        payload["due_date"] = f"{due}T00:00:00+00:00"
    result = api("PATCH", f"/cards/{card_id}", json=payload)
    console.print(f"[green]✓[/green] 카드 수정됨: [bold]{result['title']}[/bold]")


@card_cmd.command("move")
@click.argument("card_id")
@click.argument("list_id")
@click.option("--position", "-p", default=0.0, help="새 위치")
def card_move(card_id, list_id, position):
    """카드를 다른 리스트로 이동"""
    result = api("PATCH", f"/cards/{card_id}/move", json={"list_id": list_id, "position": position})
    console.print(f"[green]✓[/green] 카드 이동됨: [bold]{result['title']}[/bold] → 리스트 {list_id[:8]}")


@card_cmd.command("delete")
@click.argument("card_id")
@click.confirmation_option(prompt="정말 삭제하시겠습니까?")
def card_delete(card_id):
    """카드 삭제"""
    api("DELETE", f"/cards/{card_id}")
    console.print(f"[green]✓[/green] 카드 삭제됨")


# ── 댓글 명령어 ────────────────────────────────────────────────────────────────

@cli.group("comment")
def comment_cmd():
    """댓글 관련 명령어"""
    pass


@comment_cmd.command("add")
@click.argument("card_id")
@click.argument("content")
@click.option("--user", "-u", required=True, help="user_id (UUID)")
def comment_add(card_id, content, user):
    """카드에 댓글 추가"""
    result = api("POST", f"/cards/{card_id}/comments",
                 json={"user_id": user, "content": content})
    console.print(f"[green]✓[/green] 댓글 추가됨")


if __name__ == "__main__":
    cli()
