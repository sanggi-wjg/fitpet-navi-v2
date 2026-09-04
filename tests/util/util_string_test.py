from fitpet_navi.util.util_string import (
    find_level2_heading_outside_code_fence,
    has_level2_heading,
    normalize_section_name,
)


class NormalizeSectionNameTest:
    def test_strips_heading_prefix_and_trailing_colon(self):
        # given / when / then
        assert normalize_section_name("## 예외 조건:") == "예외 조건"
        assert normalize_section_name("  예외 조건  ") == "예외 조건"


class HasLevel2HeadingTest:
    def test_only_level2_matches(self):
        # given / when / then
        assert has_level2_heading("## 예외 조건") is True
        assert has_level2_heading("### 하위 제목") is False
        assert has_level2_heading("# 제목") is False
        assert has_level2_heading("- 본문") is False

    def test_hashtag_and_indented_code_are_not_headings(self):
        # given / when / then
        assert has_level2_heading("##긴급") is False
        assert has_level2_heading("    ## 셸 주석") is False


class FindLevel2HeadingOutsideCodeFenceTest:
    def test_returns_none_when_no_heading(self):
        # given
        text = "- 첫 줄\n### 하위 제목\n- 둘째 줄"

        # when / then
        assert find_level2_heading_outside_code_fence(text) is None

    def test_returns_first_heading_outside_fence(self):
        # given
        text = "- 첫 줄\n## 정책\n- 둘째 줄\n## 예외 조건"

        # when / then
        assert find_level2_heading_outside_code_fence(text) == "## 정책"

    def test_ignores_heading_inside_code_fence(self):
        # given
        text = "- 설명\n```bash\n## 주석처럼 보이는 줄\necho hi\n```\n- 끝"

        # when / then
        assert find_level2_heading_outside_code_fence(text) is None

    def test_detects_heading_after_fence_closes(self):
        # given
        text = "~~~\n## 코드 안\n~~~\n## 코드 밖"

        # when / then
        assert find_level2_heading_outside_code_fence(text) == "## 코드 밖"

    def test_tilde_line_does_not_close_backtick_fence(self):
        # given — 백틱 펜스 안의 `~~~` 는 코드다
        text = "```\n~~~\n## 주석\n```"

        # when / then
        assert find_level2_heading_outside_code_fence(text) is None

    def test_shorter_marker_does_not_close_longer_fence(self):
        # given — 4개짜리 펜스는 3개짜리로 닫히지 않는다
        text = "````\n```\n## 주석\n````\n## 코드 밖"

        # when / then
        assert find_level2_heading_outside_code_fence(text) == "## 코드 밖"

    def test_unclosed_fence_hides_rest_of_document(self):
        # given — 닫히지 않은 펜스는 문서 끝까지 코드다 (CommonMark)
        text = "```\n## 정책\n- x"

        # when / then
        assert find_level2_heading_outside_code_fence(text) is None

    def test_indented_code_block_heading_is_ignored(self):
        # given — 4칸 들여쓴 줄은 코드블록이다
        text = "- 설명\n\n    ## 셸 주석\n    echo hi"

        # when / then
        assert find_level2_heading_outside_code_fence(text) is None

    def test_fence_with_info_string_and_trailing_spaces(self):
        # given
        text = "  ```python  \n## 안\n```   \n## 밖"

        # when / then
        assert find_level2_heading_outside_code_fence(text) == "## 밖"
