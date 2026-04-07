# 칸반 보드에 작업 등록

현재 내가 진행 중인 작업을 칸반 보드에 등록합니다.

## 사용법

```
/kanban-add
```

## 동작

1. 현재 작업 내용을 분석합니다
2. CLI를 통해 칸반 보드에 카드로 등록합니다
3. 작업 완료 시 카드를 "Done" 컬럼으로 이동합니다

## 실행

다음 정보를 확인하고 CLI로 칸반 카드를 생성하세요:

- **작업 제목**: 현재 진행 중인 작업의 핵심 내용 (1~2줄)
- **설명**: 작업의 목적과 완료 기준
- **리스트**: 현재 상태에 맞는 컬럼 (Todo / In Progress / Done)

```bash
# 카드 추가 예시
cd /home/user/GCS/cli
python kanban.py card add <LIST_ID> "<작업 제목>" --desc "<작업 설명>"

# 작업 완료 시 Done으로 이동
python kanban.py card move <CARD_ID> <DONE_LIST_ID>
```

## 현재 작업을 등록하려면

현재 $ARGUMENTS 작업을 칸반 보드에 등록합니다.

먼저 보드 목록을 확인하세요:
```bash
cd /home/user/GCS/cli && python kanban.py board list
```

그 다음 적절한 리스트에 카드를 추가하세요:
```bash
python kanban.py card add <LIST_ID> "$ARGUMENTS"
```
