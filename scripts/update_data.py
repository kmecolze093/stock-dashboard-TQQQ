from __future__ import annotations
import json, math, time
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "latest.json"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
}
CNN_HEADERS = {
    **HEADERS,
    "Origin": "https://www.cnn.com",
    "Referer": "https://www.cnn.com/markets/fear-and-greed",
}
YAHOO = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=500d&interval=1d"
FGI = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata/{start_date}"

def get_json(url: str, headers: dict | None = None) -> dict:
    r = requests.get(url, headers=headers or HEADERS, timeout=30)
    r.raise_for_status()
    return r.json()

def fetch_yahoo(symbol: str) -> dict:
    result = get_json(YAHOO.format(symbol=symbol))["chart"]["result"][0]
    meta = result["meta"]
    raw_prices = result["indicators"]["quote"][0]["close"]
    raw_ts = result["timestamp"]
    pairs = [(ts,float(v)) for ts,v in zip(raw_ts,raw_prices) if v is not None and float(v)>0]
    timestamps=[p[0] for p in pairs]; closes=[p[1] for p in pairs]
    market_ts=int(meta["regularMarketTime"]); current=float(meta["regularMarketPrice"])
    ny=ZoneInfo("America/New_York")
    if timestamps and datetime.fromtimestamp(timestamps[-1],ny).date()==datetime.fromtimestamp(market_ts,ny).date():
        closes[-1]=current; timestamps[-1]=market_ts
    else:
        closes.append(current); timestamps.append(market_ts)
    return {"closes":closes,"timestamps":timestamps,"current":current,"market_ts":market_ts}

def sma(values:list[float], period:int=200)->list[float|None]:
    out=[None]*len(values); running=sum(values[:period])
    if len(values)<period: raise ValueError(f"{period}일선 계산에 필요한 데이터 부족({len(values)}개)")
    out[period-1]=running/period
    for i in range(period,len(values)):
        running += values[i]-values[i-period]; out[i]=running/period
    return out

def old_signal(prices, moving, timestamps):
    days=0
    for p,m,ts in zip(reversed(prices),reversed(moving),reversed(timestamps)):
        if m is None: break
        if datetime.fromtimestamp(ts,ZoneInfo("America/New_York")).weekday()>=5: continue
        if p>=m: days+=1
        else: break
    if days==0:return {"name":"200일선 아래","lines":[["TQQQ·SPYM","매도"],["SGOV","매수"]]}
    if days==1:return {"name":"200일선 위 1일 차","lines":[["TQQQ","1/3 매수"],["SGOV","일부 매도"]]}
    if days==2:return {"name":"200일선 위 2일 차","lines":[["TQQQ","2/3 매수"],["SGOV","추가 매도"]]}
    if days==3:return {"name":"200일선 위 3일 차","lines":[["TQQQ","풀매수"],["SGOV","전량 매도"]]}
    return {"name":"200일선 위","lines":[["TQQQ","유지"],["SPYM","추가매수"]]}

def beta_signal(qqq, moving, tqqq):
    above=0
    for p,m in zip(reversed(qqq),reversed(moving)):
        if m is None: break
        if p>=m*1.02: above+=1
        else: break
    cur_sma=moving[-1]; cur_q=qqq[-1]; lower=cur_sma*.98
    cycle_start=0
    for i in range(len(qqq)-1,-1,-1):
        if moving[i] is not None and qqq[i] < moving[i]*.98: cycle_start=i; break
    cycle=tqqq[cycle_start:] or [tqqq[-1]]; peak=max(cycle); dd=(tqqq[-1]-peak)/peak
    base={"is_alert":False,"drawdown_text":f"TQQQ 사이클 고점대비 {dd*100:.1f}%"}
    if dd<=-.25:return {**base,"name":f"🚨 긴급대피 발동! 고점대비 {dd*100:.1f}%","is_alert":True,"lines":[["TQQQ","절반 매도"],["SPYM","즉시 전환"]]}
    if cur_q<lower:return {**base,"name":"200일선 아래 (전량 대피)","lines":[["TQQQ·SPYM","매도"],["SGOV","매수"]]}
    if above==1:return {**base,"name":"상한선 돌파 1일 차","lines":[["TQQQ","1/3 매수"],["SGOV","일부 매도"]]}
    if above==2:return {**base,"name":"상한선 돌파 2일 차","lines":[["TQQQ","2/3 매수"],["SGOV","추가 매도"]]}
    if above==3:return {**base,"name":"상한선 돌파 3일 차","lines":[["TQQQ","풀매수"],["SGOV","전량 매도"]]}
    if above>3:return {**base,"name":f"상한선 돌파 {above}일 차 (추세 유지)","lines":[["TQQQ","보유 유지"],["SPYM","추가 매수"]]}
    return {**base,"name":"200일선 밴드 구간 (중립)","lines":[["현재 포지션","유지"],["추가 행동","없음"]]}

def fetch_fgi():
    # CNN은 자동화 요청을 차단할 수 있으므로 날짜 경로와 브라우저 헤더를 함께 사용합니다.
    start_date = (datetime.now(ZoneInfo("America/New_York")) - timedelta(days=140)).strftime("%Y-%m-%d")
    url = FGI.format(start_date=start_date)
    payload = get_json(url, headers=CNN_HEADERS)
    raw = payload.get("fear_and_greed_historical", {}).get("data", [])[-90:]
    if not raw:
        raise RuntimeError("CNN 응답에 fear_and_greed_historical.data가 없습니다.")
    vals=[float(x["y"]) for x in raw]; latest=raw[-1]; rating=str(latest.get("rating", ""))
    ko={"extreme fear":"극공포 (Extreme Fear)","fear":"공포 (Fear)","neutral":"중립 (Neutral)","greed":"탐욕 (Greed)","extreme greed":"극탐욕 (Extreme Greed)"}.get(rating.lower(),rating)
    return {"current":vals[-1],"average_30":sum(vals[-30:])/len(vals[-30:]),"rating":rating,"rating_ko":ko,"values":vals}

def load_previous_fgi():
    if not OUT.exists():
        return None
    try:
        previous = json.loads(OUT.read_text(encoding="utf-8"))
        return previous.get("fgi")
    except (OSError, json.JSONDecodeError):
        return None

def main():
    qqq=fetch_yahoo("QQQ"); time.sleep(.4); tqqq=fetch_yahoo("TQQQ")
    try:
        fgi = fetch_fgi()
    except Exception as exc:
        fgi = load_previous_fgi()
        if fgi is None:
            raise
        print(f"warning: CNN FGI 갱신 실패, 이전 값을 유지합니다: {exc}")
    qma=sma(qqq["closes"]); tma=sma(tqqq["closes"])
    size=90
    data={
      "updated_at_kst":datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y-%m-%d %H:%M KST"),
      "market_date":datetime.fromtimestamp(qqq["market_ts"],ZoneInfo("America/New_York")).strftime("%Y-%m-%d"),
      "beta":{"prices":qqq["closes"][-size:],"upper":[x*1.02 for x in qma[-size:]],"lower":[x*.98 for x in qma[-size:]],"current_price":qqq["current"],"sma_200":qma[-1],"signal":beta_signal(qqq["closes"],qma,tqqq["closes"])},
      "old":{"prices":tqqq["closes"][-size:],"sma":tma[-size:],"current_price":tqqq["current"],"sma_200":tma[-1],"gap_pct":(tqqq["current"]-tma[-1])/tma[-1]*100,"signal":old_signal(tqqq["closes"],tma,tqqq["timestamps"])},
      "fgi":fgi
    }
    OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"updated {OUT}")
if __name__=="__main__": main()
