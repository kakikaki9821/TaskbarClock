"""Unit tests for clock rendering angle calculations."""

from ui.clock_renderer import hour_hand_angle, minute_hand_angle, second_hand_angle


class TestHourHandAngle:
    def test_at_12(self) -> None:
        assert hour_hand_angle(12, 0) == 0.0

    def test_at_0(self) -> None:
        assert hour_hand_angle(0, 0) == 0.0

    def test_at_3(self) -> None:
        assert hour_hand_angle(3, 0) == 90.0

    def test_at_6(self) -> None:
        assert hour_hand_angle(6, 0) == 180.0

    def test_at_9(self) -> None:
        assert hour_hand_angle(9, 0) == 270.0

    def test_includes_minutes(self) -> None:
        # 3:30 = 3*30 + 30/60*30 = 90 + 15 = 105
        assert hour_hand_angle(3, 30) == 105.0

    def test_at_12_30(self) -> None:
        assert hour_hand_angle(12, 30) == 15.0

    def test_at_15(self) -> None:
        # 15:00 = 3:00 PM = 90°
        assert hour_hand_angle(15, 0) == 90.0


class TestMinuteHandAngle:
    def test_at_0(self) -> None:
        assert minute_hand_angle(0) == 0.0

    def test_at_15(self) -> None:
        assert minute_hand_angle(15) == 90.0

    def test_at_30(self) -> None:
        assert minute_hand_angle(30) == 180.0

    def test_at_45(self) -> None:
        assert minute_hand_angle(45) == 270.0

    def test_includes_seconds(self) -> None:
        # 15:30 = 15*6 + 30/60*6 = 90 + 3 = 93
        assert minute_hand_angle(15, 30) == 93.0


class TestSecondHandAngle:
    def test_at_0(self) -> None:
        assert second_hand_angle(0) == 0.0

    def test_at_15(self) -> None:
        assert second_hand_angle(15) == 90.0

    def test_at_30(self) -> None:
        assert second_hand_angle(30) == 180.0

    def test_at_45(self) -> None:
        assert second_hand_angle(45) == 270.0

    def test_smooth_with_milliseconds(self) -> None:
        # 30s 500ms = 30*6 + 0.5*6 = 180 + 3 = 183
        assert second_hand_angle(30, 500) == 183.0
