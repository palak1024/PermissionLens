from .risk_engine import calculate_risk
from .ai_explainer import generate_ai_summary


def analyze(apk_data, include_ai=True):
    """
    Complete Person-3 pipeline:
    Androguard-normalized data -> risk engine -> AI explanation.
    """
    risk_result = calculate_risk(apk_data)

    result = {
        **risk_result,
        "ai_summary": None,
    }

    if include_ai:
        result["ai_summary"] = generate_ai_summary(apk_data, risk_result)

    return result
