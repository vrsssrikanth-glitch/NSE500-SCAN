def fundamental_summary(info):
    roe = info.get("returnOnEquity", 0) * 100
    de = info.get("debtToEquity", None)
    promoter = info.get("heldPercentInsiders", 0) * 100

    passed = 0
    if roe >= 10:
        passed += 1
    if de is not None and de <= 1.5:
        passed += 1
    if promoter >= 20:
        passed += 1

    return {
        "ROE (%)": round(roe, 2),
        "Debt/Equity": de,
        "Promoter Holding (%)": round(promoter, 2),
        "Fundamental Pass": passed >= 2
    }