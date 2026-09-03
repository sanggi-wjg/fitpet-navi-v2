from dataclasses import dataclass
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, field_validator
from pydantic_core.core_schema import ValidationInfo

from fitpet_navi.util.util_string import has_level2_heading, normalize_section_name


class NoChange(BaseModel):
    """수정할 것이 없거나, 담당자에게 되물어야 할 때의 탈출구."""

    model_config = ConfigDict(extra="forbid")

    tool: Literal["no_change"]
    message: str = Field(min_length=1)


class ReplaceSection(BaseModel):
    """섹션을 새 내용으로 교체한다."""

    model_config = ConfigDict(extra="forbid")

    tool: Literal["replace_section"]
    section: str = Field(min_length=1)
    new_content: str = Field(min_length=1)
    reason: str = Field(min_length=1)

    @field_validator("section")
    @classmethod
    def normalize_section(cls, value: str) -> str:
        normalized = normalize_section_name(value)
        if not normalized:
            raise ValueError("section이 비어 있다. 문서에 있는 `## ` 헤딩 이름을 그대로 써야 한다.")
        return normalized

    @field_validator("new_content")
    @classmethod
    def strip_heading(cls, value: str, info: ValidationInfo) -> str:
        section = info.data.get("section")
        lines = value.strip().splitlines()
        if section and lines and has_level2_heading(lines[0].strip()):
            if normalize_section_name(lines[0]) == section:
                lines = lines[1:]

        stripped = "\n".join(lines).strip()
        if not stripped:
            raise ValueError("new_content가 비어 있다. 섹션을 비우려면 no_change 로 담당자에게 먼저 물어야 한다.")
        return stripped


# update_field(제목·태그)는 보류 — 제목·태그 수정은 no_change 의 message 로 담당자에게 제안하고, 담당자가 직접 고친다.
ProposalPayload = Annotated[NoChange | ReplaceSection, Field(discriminator="tool")]
PROPOSAL_ADAPTER: TypeAdapter[ProposalPayload] = TypeAdapter(ProposalPayload)
PROPOSAL_JSON_SCHEMA: dict[str, Any] = PROPOSAL_ADAPTER.json_schema()


@dataclass(frozen=True)
class RejectionContext:
    """거부 후 재요청 맥락"""

    previous_proposal_json: str
    reason: str


@dataclass(frozen=True)
class ProposalResult:
    payload: ProposalPayload
