from fitpet_navi.util.util_diff import unified_diff


class UnifiedDiffTest:
    def test_same_text_returns_empty(self):
        # given
        text = "- 마케팅 수신 동의를 하지 않은 유저는 제외"

        # when / then
        assert unified_diff(text, text, name="예외 조건") == ""

    def test_added_and_removed_lines_are_marked(self):
        # given
        before = "- 첫 줄\n- 둘째 줄"
        after = "- 첫 줄\n- 셋째 줄"

        # when
        result = unified_diff(before, after, name="예외 조건")

        # then
        lines = result.splitlines()
        assert lines[0] == "--- 예외 조건"
        assert lines[1] == "+++ 예외 조건"
        assert "-- 둘째 줄" in lines
        assert "+- 셋째 줄" in lines
        assert " - 첫 줄" in lines  # 유지된 줄은 공백 접두

    def test_missing_trailing_newline_does_not_break_output(self):
        # given
        before = "- a"
        after = "- a\n- b"

        # when
        result = unified_diff(before, after)

        # then
        assert result.endswith("+- b\n")
        assert "\\ No newline" not in result
