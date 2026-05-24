from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class Turn:
    role: str
    content: str
    filters: dict[str, Any] = field(default_factory=dict)
    tools_used: list[str] = field(default_factory=list)


@dataclass
class SessionState:
    session_id: str
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    turns: list[Turn] = field(default_factory=list)
    active_filters: dict[str, Any] = field(default_factory=dict)
    last_candidate_ids: list[str] = field(default_factory=list)
    last_recommendations: list[dict[str, Any]] = field(default_factory=list)

    def add_turn(self, role: str, content: str, filters: dict, tools_used: list[str], max_turns: int) -> None:
        self.turns.append(
            Turn(role=role, content=content, filters=filters.copy(), tools_used=tools_used)
        )
        if len(self.turns) > max_turns:
            self.turns = self.turns[-max_turns:]

    def history_summary(self) -> str:
        if not self.turns:
            return "No prior conversation."
        lines = []
        for t in self.turns[-5:]:
            tools = f" [tools: {', '.join(t.tools_used)}]" if t.tools_used else ""
            lines.append(f"{t.role}: {t.content}{tools}")
        return "\n".join(lines)


class SessionMemory:
    """In-memory session store keyed by session ID."""

    def __init__(self, max_turns: int = 10):
        self._sessions: dict[str, SessionState] = {}
        self.max_turns = max_turns

    def count(self) -> int:
        return len(self._sessions)

    def get(self, session_id: str) -> SessionState | None:
        return self._sessions.get(session_id)

    def get_or_create(self, session_id: str | None) -> tuple[str, SessionState]:
        if session_id and session_id in self._sessions:
            return session_id, self._sessions[session_id]
        new_id = session_id or str(uuid.uuid4())
        state = SessionState(session_id=new_id)
        self._sessions[new_id] = state
        return new_id, state

    def delete(self, session_id: str) -> bool:
        return self._sessions.pop(session_id, None) is not None
