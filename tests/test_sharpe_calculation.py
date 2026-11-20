import math

import pandas as pd
import pytest

from metrics import calculate_sharpe_ratio


def make_equity(values: list[float]) -> pd.Series:
    """Equity curve with one business day per value."""
    dates = pd.date_range("2024-01-01", periods=len(values), freq="B")
    return pd.Series(values, index=dates)


# Daily returns +1%, -1%, +2%:
#   100 -> 101 (+1%) -> 99.99 (-1%) -> 101.9898 (+2%)
# Mean = 0.02 / 3 = 1/150
# Sample variance = ((1/300)^2 + (1/60)^2 + (1/75)^2) / 2 = 7/30000
# Sharpe (periods_per_year=1) = (1/150) / sqrt(7/30000) = 2 / sqrt(21) ≈ 0.4364
KNOWN_EQUITY = [100, 101, 99.99, 101.9898]


def test_sharpe_matches_hand_calculation():
    result = calculate_sharpe_ratio(make_equity(KNOWN_EQUITY), periods_per_year=1)

    assert result == pytest.approx(2 / math.sqrt(21))


def test_sharpe_is_annualized_by_sqrt_periods_per_year():
    result = calculate_sharpe_ratio(make_equity(KNOWN_EQUITY), periods_per_year=252)

    assert result == pytest.approx(2 / math.sqrt(21) * math.sqrt(252))


def test_sharpe_subtracts_risk_free_rate():
    # Per-period risk-free rate = 0.01 / 1 = 0.01
    # Mean excess return = 1/150 - 1/100 = -1/300
    # Sharpe = (-1/300) / sqrt(7/30000) = -1 / sqrt(21)
    result = calculate_sharpe_ratio(
        make_equity(KNOWN_EQUITY), risk_free_rate=0.01, periods_per_year=1
    )

    assert result == pytest.approx(-1 / math.sqrt(21))


def test_sharpe_is_nan_for_flat_equity():
    result = calculate_sharpe_ratio(make_equity([100, 100, 100, 100]))

    assert math.isnan(result)


def test_sharpe_is_nan_for_constant_growth():
    # Every return is 10%, so volatility is zero in theory but rounding
    # leaves a tiny value. This checks the tolerance in the zero check.
    result = calculate_sharpe_ratio(make_equity([100, 110, 121, 133.1]))

    assert math.isnan(result)


def test_sharpe_rejects_too_few_values():
    with pytest.raises(ValueError):
        calculate_sharpe_ratio(make_equity([100, 110]))


def test_sharpe_rejects_invalid_periods_per_year():
    with pytest.raises(ValueError):
        calculate_sharpe_ratio(make_equity(KNOWN_EQUITY), periods_per_year=0)