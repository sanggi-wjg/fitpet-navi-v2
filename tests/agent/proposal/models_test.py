import json

import pytest
from pydantic import ValidationError

from fitpet_navi.agent.proposal.models import PROPOSAL_ADAPTER, ReplaceSection


def _replace_section(section: str, new_content: str) -> ReplaceSection:
    raw = json.dumps({"tool": "replace_section", "section": section, "new_content": new_content, "reason": "r"})
    payload = PROPOSAL_ADAPTER.validate_json(raw)
    assert isinstance(payload, ReplaceSection)
    return payload


class ReplaceSectionValidatorTest:
    def test_leading_same_section_heading_is_stripped(self):
        # given / when
        payload = _replace_section("예외 조건", "## 예외 조건\n- a\n- b")

        # then
        assert payload.new_content == "- a\n- b"

    def test_sub_heading_and_code_fence_are_kept(self):
        # given
        content = "### 세부\n- a\n```bash\n## 주석\n```"

        # when
        payload = _replace_section("예외 조건", content)

        # then
        assert payload.new_content == content

    def test_other_level2_heading_is_rejected(self):
        # given / when / then
        with pytest.raises(ValidationError, match="## 정책"):
            _replace_section("예외 조건", "## 정책\n- a\n\n## 예외 조건\n- b")

    def test_level2_heading_in_middle_is_rejected(self):
        # given / when / then
        with pytest.raises(ValidationError, match="## 대상"):
            _replace_section("예외 조건", "- a\n## 대상\n- b")

    def test_empty_content_after_stripping_is_rejected(self):
        # given / when / then
        with pytest.raises(ValidationError, match="비어 있다"):
            _replace_section("예외 조건", "## 예외 조건\n\n")
