// ===== Indicator Info Data =====
const indicatorInfo = {
  sma: {
    title: 'SMA (Simple Moving Average) — 단순이동평균선',
    html: `
      <h4>개념</h4>
      <p>일정 기간 동안의 종가 평균을 계산하여 추세를 파악하는 가장 기본적인 기술적 지표입니다. 단기(50일)와 장기(200일) 이동평균선의 교차를 통해 매매 시점을 판단합니다.</p>

      <h4>계산 공식</h4>
      <div class="formula">SMA(n) = (P₁ + P₂ + ... + Pₙ) / n</div>

      <h4>경제적 의미</h4>
      <ul>
        <li><strong>Golden Cross (골든크로스)</strong>: 단기선(50일)이 장기선(200일)을 상향 돌파 → 상승 추세 전환 신호</li>
        <li><strong>Death Cross (데드크로스)</strong>: 단기선이 장기선을 하향 돌파 → 하락 추세 전환 신호</li>
        <li>이동평균선 위에 있는 가격 = 해당 기간 매수자들이 평균적으로 수익 중</li>
      </ul>

      <h4>봇에서의 활용</h4>
      <p><span class="tag buy">BUY</span> SMA50 &gt; SMA200 (골든크로스 상태)</p>
      <p><span class="tag sell">SELL</span> SMA50 &lt; SMA200 (데드크로스 상태)</p>
      <p><span class="tag info">참고</span> 주간(Weekly) 차트의 SMA도 함께 확인하여 다중 타임프레임 정렬을 검증합니다.</p>
    `
  },
  rsi: {
    title: 'RSI (Relative Strength Index) — 상대강도지수',
    html: `
      <h4>개념</h4>
      <p>일정 기간(14일) 동안의 상승폭과 하락폭을 비교하여 현재 가격이 과매수인지 과매도인지를 0~100 사이 수치로 나타내는 모멘텀 지표입니다.</p>

      <h4>계산 공식</h4>
      <div class="formula">RSI = 100 - (100 / (1 + RS))
RS = 평균 상승폭 / 평균 하락폭</div>

      <h4>경제적 의미</h4>
      <ul>
        <li><strong>RSI &gt; 70 (과매수)</strong>: 가격이 단기간 과도하게 상승. 매도 압력이 커질 가능성</li>
        <li><strong>RSI &lt; 30 (과매도)</strong>: 가격이 단기간 과도하게 하락. 반등 가능성</li>
        <li><strong>RSI 30~70</strong>: 정상 범위. 추세에 따라 매매 가능</li>
        <li>다이버전스(가격은 신고가이나 RSI는 하락)는 추세 약화 신호</li>
      </ul>

      <h4>봇에서의 활용</h4>
      <p><span class="tag buy">BUY</span> RSI &lt; 70 (과매수 아님)</p>
      <p><span class="tag sell">SELL</span> RSI &gt; 70 (과매수 구간 진입)</p>
    `
  },
  vol_osc: {
    title: 'Volume Oscillator — 거래량 오실레이터',
    html: `
      <h4>개념</h4>
      <p>단기(5일)와 장기(20일) 거래량 이동평균의 차이를 비율로 나타낸 지표입니다. 거래량의 방향성과 강도를 측정합니다.</p>

      <h4>계산 공식</h4>
      <div class="formula">Vol_Osc = ((Vol_SMA5 - Vol_SMA20) / Vol_SMA20) × 100%</div>

      <h4>경제적 의미</h4>
      <ul>
        <li><strong>양수(+)</strong>: 최근 거래량이 평소보다 많음 → 현재 추세에 대한 시장 참여자들의 관심 증가</li>
        <li><strong>음수(-)</strong>: 최근 거래량이 평소보다 적음 → 시장 관심 감소, 추세 약화 가능</li>
        <li>가격 상승 + 거래량 증가 = 건강한 상승세 (진짜 매수세)</li>
        <li>가격 상승 + 거래량 감소 = 상승세 약화 가능 (주의)</li>
      </ul>

      <h4>봇에서의 활용</h4>
      <p><span class="tag buy">BUY</span> Volume Oscillator &gt; 0 (거래량 확인)</p>
    `
  },
  macd: {
    title: 'MACD (Moving Average Convergence Divergence)',
    html: `
      <h4>개념</h4>
      <p>두 개의 지수이동평균(EMA) 간의 차이를 이용하여 추세의 방향, 강도, 전환점을 파악하는 추세 추종 모멘텀 지표입니다.</p>

      <h4>구성 요소</h4>
      <div class="formula">MACD Line = EMA(12) - EMA(26)
Signal Line = EMA(9) of MACD Line
Histogram = MACD Line - Signal Line</div>

      <h4>경제적 의미</h4>
      <ul>
        <li><strong>MACD &gt; Signal</strong>: 상승 모멘텀이 강해지는 중 → 매수 신호</li>
        <li><strong>MACD &lt; Signal</strong>: 하락 모멘텀이 강해지는 중 → 매도 신호</li>
        <li><strong>Histogram 증가</strong>: 현재 추세가 가속 중</li>
        <li><strong>Zero Line 돌파</strong>: 추세 방향 전환의 중요한 신호</li>
        <li>가격 대비 MACD 다이버전스는 추세 전환 예고</li>
      </ul>

      <h4>봇에서의 활용</h4>
      <p><span class="tag buy">BUY</span> MACD &gt; Signal Line</p>
      <p><span class="tag sell">SELL</span> MACD &lt; Signal Line</p>
    `
  },
  bb: {
    title: 'Bollinger Bands — 볼린저 밴드',
    html: `
      <h4>개념</h4>
      <p>이동평균선을 중심으로 표준편차(σ)를 이용해 상단/하단 밴드를 설정하여, 가격의 상대적 위치와 변동성을 측정하는 지표입니다.</p>

      <h4>계산 공식</h4>
      <div class="formula">Middle Band = SMA(20)
Upper Band = SMA(20) + 2σ
Lower Band = SMA(20) - 2σ
%Band = (Price - Lower) / (Upper - Lower)</div>

      <h4>경제적 의미</h4>
      <ul>
        <li><strong>%Band &gt; 95%</strong>: 상단밴드 근접 → 과매수 가능성, 저항 영역</li>
        <li><strong>%Band &lt; 5%</strong>: 하단밴드 근접 → 과매도 가능성, 지지 영역</li>
        <li><strong>밴드 수축 (Squeeze)</strong>: 변동성 감소 → 큰 움직임 예고</li>
        <li><strong>밴드 확장</strong>: 변동성 증가 → 추세 진행 중</li>
        <li>통계적으로 가격의 약 95%가 밴드 내에서 움직임</li>
      </ul>

      <h4>봇에서의 활용</h4>
      <p><span class="tag buy">BUY</span> %Band &lt; 0.95 (상단밴드 미도달)</p>
      <p><span class="tag sell">SELL</span> %Band &gt; 0.95 (상단밴드 도달)</p>
    `
  },
  stoch: {
    title: 'Stochastic Oscillator — 스토캐스틱',
    html: `
      <h4>개념</h4>
      <p>현재 가격이 일정 기간(14일)의 가격 범위 중 어디에 위치하는지를 0~100%로 나타내는 모멘텀 지표입니다. %K(빠른선)와 %D(느린선)로 구성됩니다.</p>

      <h4>계산 공식</h4>
      <div class="formula">%K = ((현재가 - 14일 최저) / (14일 최고 - 14일 최저)) × 100
%D = %K의 3일 이동평균</div>

      <h4>경제적 의미</h4>
      <ul>
        <li><strong>%K &gt; 80 (과매수)</strong>: 14일 중 최고가 근처 → 단기 조정 가능성</li>
        <li><strong>%K &lt; 20 (과매도)</strong>: 14일 중 최저가 근처 → 반등 가능성</li>
        <li><strong>%K가 %D를 상향돌파</strong>: 매수 신호</li>
        <li><strong>%K가 %D를 하향돌파</strong>: 매도 신호</li>
        <li>상승 추세에서는 과매수 구간이 오래 지속될 수 있음</li>
      </ul>

      <h4>봇에서의 활용</h4>
      <p><span class="tag buy">BUY</span> Stoch_K &lt; 80 (과매수 아님)</p>
      <p><span class="tag sell">SELL</span> Stoch_K &gt; 80 (과매수)</p>
    `
  },
  adx: {
    title: 'ADX (Average Directional Index) — 평균방향지수',
    html: `
      <h4>개념</h4>
      <p>추세의 <strong>강도</strong>를 측정하는 지표입니다. 방향(상승/하락)은 알려주지 않고, 추세가 얼마나 강한지만 0~100으로 나타냅니다.</p>

      <h4>계산 원리</h4>
      <div class="formula">+DI: 상승 방향 지표 (양의 방향 움직임)
-DI: 하락 방향 지표 (음의 방향 움직임)
ADX = Smoothed(|+DI - -DI| / (+DI + -DI)) × 100</div>

      <h4>경제적 의미</h4>
      <ul>
        <li><strong>ADX &gt; 25</strong>: 강한 추세 존재 → 추세 추종 전략 유효</li>
        <li><strong>ADX &lt; 25</strong>: 약한 추세 또는 횡보 → 레인지 전략 고려</li>
        <li><strong>ADX &gt; 50</strong>: 매우 강한 추세 (드물지만 강력한 신호)</li>
        <li>ADX가 상승 중 = 추세가 강해지는 중</li>
        <li>ADX가 하락 중 = 추세가 약해지는 중</li>
      </ul>

      <h4>봇에서의 활용</h4>
      <p><span class="tag buy">BUY 조건</span> ADX &gt; 25 (강한 추세가 존재할 때만 매수)</p>
      <p><span class="tag info">핵심</span> 다른 지표의 방향 신호를 ADX로 확인하여 가짜 신호를 필터링합니다.</p>
    `
  },
  mfi: {
    title: 'MFI (Money Flow Index) — 자금흐름지수',
    html: `
      <h4>개념</h4>
      <p>RSI와 유사하지만 <strong>거래량을 함께 고려</strong>하는 지표입니다. "거래량 가중 RSI"라고도 불리며, 자금의 유입/유출을 측정합니다.</p>

      <h4>계산 공식</h4>
      <div class="formula">Typical Price = (High + Low + Close) / 3
Money Flow = Typical Price × Volume
Positive/Negative MF 구분 후 비율 계산
MFI = 100 - (100 / (1 + Money Flow Ratio))</div>

      <h4>경제적 의미</h4>
      <ul>
        <li><strong>MFI &gt; 80 (과매수)</strong>: 대량의 자금이 유입된 상태 → 매수세 소진 가능</li>
        <li><strong>MFI &lt; 20 (과매도)</strong>: 대량의 자금이 유출된 상태 → 매도세 소진 가능</li>
        <li>RSI보다 거래량 정보를 포함하므로 더 신뢰성 높은 과매수/과매도 판단</li>
        <li>기관 투자자의 매수/매도를 간접적으로 추적 가능</li>
      </ul>

      <h4>봇에서의 활용</h4>
      <p><span class="tag buy">BUY</span> MFI &lt; 80 (과매수 아님)</p>
      <p><span class="tag info">특징</span> 거래량이 많은 종목에서 특히 유용합니다.</p>
    `
  },
  obv: {
    title: 'OBV (On-Balance Volume) — 거래량 균형',
    html: `
      <h4>개념</h4>
      <p>가격 변동 방향에 따라 거래량을 누적하여, 자금의 유입/유출 추세를 파악하는 선행 지표입니다. "Smart Money"의 움직임을 추적하는 데 사용됩니다.</p>

      <h4>계산 공식</h4>
      <div class="formula">가격 상승일: OBV = 전일 OBV + 당일 거래량
가격 하락일: OBV = 전일 OBV - 당일 거래량
가격 변동 없음: OBV = 전일 OBV</div>

      <h4>경제적 의미</h4>
      <ul>
        <li><strong>OBV 상승</strong>: 상승일에 거래량이 더 많음 → 매수세(자금 유입) 우위</li>
        <li><strong>OBV 하락</strong>: 하락일에 거래량이 더 많음 → 매도세(자금 유출) 우위</li>
        <li><strong>OBV &gt; OBV SMA5</strong>: 최근 자금 유입 가속화</li>
        <li>가격은 횡보인데 OBV 상승 → 조만간 가격 상승 가능 (축적 단계)</li>
        <li>가격은 상승인데 OBV 하락 → 상승세 약화 경고 (분배 단계)</li>
      </ul>

      <h4>봇에서의 활용</h4>
      <p><span class="tag buy">BUY</span> OBV &gt; OBV SMA(5) (거래량 유입 확인)</p>
    `
  },
  regime: {
    title: '시장 레짐 (Market Regime) — VIX + SPY 기반',
    html: `
      <h4>개념</h4>
      <p>VIX(변동성 지수)와 SPY(S&P 500 ETF)의 이동평균 추세를 결합하여 현재 시장 환경을 4단계로 분류합니다.</p>

      <h4>VIX 구간 분류</h4>
      <div class="formula">🔵 LOW_VOL:     VIX < 15  (낮은 변동성, 안정적)
🟢 NORMAL:      VIX 15~25 (정상 변동성)
🟠 HIGH_VOL:    VIX 25~35 (높은 변동성, 주의)
🔴 EXTREME_FEAR: VIX > 35  (공포 구간, 위험)</div>

      <h4>경제적 의미</h4>
      <ul>
        <li><strong>VIX</strong>: "공포 지수"로 불리며, S&P 500 옵션의 내재 변동성에서 산출</li>
        <li><strong>VIX 상승</strong>: 시장 불확실성/공포 증가 → 포지션 축소 고려</li>
        <li><strong>VIX 하락</strong>: 시장 안정/낙관 → 적극적 매매 가능</li>
        <li><strong>SPY BULL(SMA50 > SMA200)</strong>: 대형주 상승 추세 → 롱 전략 유리</li>
        <li><strong>SPY BEAR(SMA50 < SMA200)</strong>: 대형주 하락 추세 → 방어적 전략</li>
      </ul>

      <h4>봇에서의 활용</h4>
      <p><span class="tag info">전략</span> 시장 레짐에 따라 포지션 크기와 리스크 허용도를 조절합니다. EXTREME_FEAR에서는 매수를 자제합니다.</p>
    `
  },
  sentiment: {
    title: 'AI 감성 분석 (Sentiment Analysis)',
    html: `
      <h4>개념</h4>
      <p>AI(Claude/Ollama)를 활용하여 최신 뉴스 기사의 감성을 -1.0(극도로 부정)부터 +1.0(극도로 긍정)까지 수치화합니다.</p>

      <h4>분석 방법</h4>
      <div class="formula">1. Yahoo Finance에서 최신 뉴스 5개 수집
2. 각 뉴스를 LLM이 -1.0 ~ +1.0으로 평가
3. 시간 가중치 적용 (최신 뉴스일수록 높은 가중치)
4. 가중 평균 감성 점수 산출

Weight = e^(-0.5 × index)  // 지수 감쇠</div>

      <h4>경제적 의미</h4>
      <ul>
        <li><strong>점수 &gt; +0.3</strong>: 긍정적 뉴스 다수 → 매수에 우호적 환경</li>
        <li><strong>점수 &lt; -0.3</strong>: 부정적 뉴스 다수 → 매도/관망 고려</li>
        <li>뉴스 감성은 주가의 단기 방향에 선행하는 경향</li>
        <li>어닝 서프라이즈, M&A, 규제 변화 등 이벤트 감지</li>
      </ul>

      <h4>봇에서의 활용</h4>
      <p><span class="tag buy">BUY 조건</span> 가중 감성 &gt; +0.3</p>
      <p><span class="tag sell">SELL 조건</span> 가중 감성 &lt; -0.3</p>
    `
  },
  risk: {
    title: '리스크 관리 — ATR 기반 손익 설정',
    html: `
      <h4>개념</h4>
      <p>ATR(평균 실제 범위)을 기반으로 변동성에 비례한 손절(Stop Loss)과 익절(Take Profit) 가격을 동적으로 설정합니다.</p>

      <h4>계산 공식</h4>
      <div class="formula">Stop Loss  = 현재가 - (ATR × 2.0)
Take Profit = 현재가 + (ATR × 4.0)
Risk/Reward = (TP - 현재가) / (현재가 - SL)</div>

      <h4>경제적 의미</h4>
      <ul>
        <li><strong>ATR 기반 손절</strong>: 변동성이 큰 종목은 넓은 손절, 작은 종목은 좁은 손절 → 과도한 손절 방지</li>
        <li><strong>R:R 비율 2:1</strong>: 승률 50%로도 수익 가능한 구조</li>
        <li>고정 퍼센트 손절보다 시장 변동성에 적응적</li>
      </ul>

      <h4>봇에서의 활용</h4>
      <p><span class="tag info">배수</span> SL = ATR × 2.0 / TP = ATR × 4.0 (기본 설정)</p>
    `
  },
  atr: {
    title: 'ATR (Average True Range) — 평균 실제 범위',
    html: `
      <h4>개념</h4>
      <p>일정 기간(14일) 동안 주가의 실제 변동 범위를 평균한 값으로, 종목의 <strong>변동성</strong>을 측정합니다.</p>

      <h4>계산 공식</h4>
      <div class="formula">True Range = max(
  고가 - 저가,
  |고가 - 전일 종가|,
  |저가 - 전일 종가|
)
ATR = TR의 14일 이동평균</div>

      <h4>경제적 의미</h4>
      <ul>
        <li>ATR이 높을수록 변동성이 큼 → 리스크 高, 수익 기회도 高</li>
        <li>ATR이 낮을수록 변동성이 작음 → 안정적이지만 수익 기회 限</li>
        <li>ATR 상승 = 시장 불확실성 증가</li>
        <li>ATR 하락 = 시장 안정화</li>
      </ul>

      <h4>봇에서의 활용</h4>
      <p><span class="tag info">용도</span> 손절/익절 가격 산정, 포지션 사이징의 핵심 변수입니다.</p>
    `
  },
  kelly: {
    title: 'Kelly Criterion — 켈리 기준',
    html: `
      <h4>개념</h4>
      <p>장기적으로 자산을 최대화하기 위한 수학적 최적 베팅 비율입니다. 승률과 손익비를 기반으로 전체 자본의 몇 %를 투자할지 결정합니다.</p>

      <h4>계산 공식</h4>
      <div class="formula">f* = (b × p - q) / b

b = 평균 수익 / 평균 손실 (손익비)
p = 승률
q = 패률 (1 - p)

실제 적용: Half-Kelly (f*/2), 최대 25% 제한</div>

      <h4>경제적 의미</h4>
      <ul>
        <li><strong>Kelly %가 높을수록</strong>: 통계적으로 유리한 기회 → 더 많은 자본 투입 가능</li>
        <li><strong>Kelly %가 낮을수록</strong>: 리스크 대비 보상 적음 → 소규모 투자</li>
        <li><strong>Kelly %가 0 이하</strong>: 투자하지 않는 것이 최적</li>
        <li><strong>Half-Kelly 사용 이유</strong>: Full Kelly는 이론적 최적이나 실전에서는 변동성이 과도하여 절반만 적용</li>
      </ul>

      <h4>봇에서의 활용</h4>
      <p><span class="tag info">범위</span> 0% ~ 25% (Half-Kelly, 상한 제한)</p>
      <p><span class="tag info">목적</span> 과도한 집중 투자를 방지하면서 수학적으로 최적에 가까운 포지션 크기를 결정합니다.</p>
    `
  },
  fib: {
    title: 'Fibonacci Retracement — 피보나치 되돌림',
    html: `
      <h4>개념</h4>
      <p>52주 고점에서 저점까지의 가격 범위에 피보나치 비율(23.6%, 38.2%, 50%, 61.8%, 78.6%)을 적용하여 잠재적 지지/저항 수준을 파악합니다.</p>

      <h4>주요 레벨</h4>
      <div class="formula">0.0%   = 52주 고점 (시작점)
23.6%  = 얕은 되돌림
38.2%  = 일반적 되돌림
50.0%  = 중간 되돌림
61.8%  = 황금 비율 (가장 중요)
78.6%  = 깊은 되돌림
100.0% = 52주 저점 (완전 되돌림)</div>

      <h4>경제적 의미</h4>
      <ul>
        <li><strong>38.2% ~ 61.8%</strong>: 가장 빈번하게 반등이 일어나는 구간</li>
        <li><strong>61.8% (황금 비율)</strong>: 가장 중요한 지지/저항선으로, 많은 트레이더가 주목</li>
        <li>이 레벨에서 반등 시 → 강한 지지 확인</li>
        <li>이 레벨을 이탈 시 → 다음 레벨까지 추가 하락 가능</li>
        <li>자기충족적 예언(Self-fulfilling prophecy): 많은 시장 참여자가 사용하므로 실제로 작동하는 경향</li>
      </ul>

      <h4>봇에서의 활용</h4>
      <p><span class="tag info">용도</span> 현재가 대비 지지/저항 수준 확인 및 목표가 설정에 참고합니다.</p>
    `
  },
  rs: {
    title: '상대강도 (Relative Strength vs SPY)',
    html: `
      <h4>개념</h4>
      <p>개별 종목의 수익률을 S&P 500 대표 ETF(SPY)와 비교하여, 시장 대비 얼마나 강한(또는 약한)지를 측정합니다.</p>

      <h4>계산 방법</h4>
      <div class="formula">상대 수익률 = 종목 수익률 - SPY 수익률

1개월/3개월 기간 각각 비교
Outperform: 종목 수익률 > SPY 수익률
Underperform: 종목 수익률 < SPY 수익률</div>

      <h4>경제적 의미</h4>
      <ul>
        <li><strong>아웃퍼폼</strong>: 시장 전체보다 강한 종목 → 기관/투자자 관심 집중, 추가 상승 가능성</li>
        <li><strong>언더퍼폼</strong>: 시장 전체보다 약한 종목 → 구조적 약점 가능성, 추가 하락 주의</li>
        <li>"강한 주식은 더 강해지고, 약한 주식은 더 약해진다" (모멘텀 효과)</li>
        <li>섹터 로테이션을 파악하는 데도 활용 가능</li>
      </ul>

      <h4>봇에서의 활용</h4>
      <p><span class="tag buy">BUY 필터</span> SPY 대비 아웃퍼폼 종목만 매수 대상으로 고려합니다.</p>
    `
  }
};

// ===== Modal Logic =====
const modalOverlay = document.getElementById('modalOverlay');
const infoModal = document.getElementById('infoModal');
const modalTitle = document.getElementById('modalTitle');
const modalBody = document.getElementById('modalBody');
const modalClose = document.getElementById('modalClose');

function openInfoModal(indicatorKey) {
  const info = indicatorInfo[indicatorKey];
  if (!info) return;
  modalTitle.textContent = info.title;
  modalBody.innerHTML = info.html;
  modalOverlay.classList.add('active');
  document.body.style.overflow = 'hidden';
}

function closeInfoModal() {
  modalOverlay.classList.remove('active');
  document.body.style.overflow = '';
}

// Event delegation for info buttons
document.addEventListener('click', (e) => {
  const infoBtn = e.target.closest('.info-btn');
  if (infoBtn) {
    const key = infoBtn.dataset.indicator;
    if (key) openInfoModal(key);
    return;
  }
});

modalClose.addEventListener('click', closeInfoModal);
modalOverlay.addEventListener('click', (e) => {
  if (e.target === modalOverlay) closeInfoModal();
});

document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') closeInfoModal();
});

// ===== API Base URL =====
// When served via api_server.py (port 8000), use same origin.
// When served via npx serve (port 3000), point to API server.
const API_BASE = window.location.port === '8000' ? '' : 'http://localhost:8000';

// ===== Chart Drawing =====
let chartPrices = [];
let chartSma50 = [];
let chartSma200 = [];

function drawChart(prices, sma50, sma200) {
  if (prices && prices.length) {
    chartPrices = prices;
    chartSma50 = sma50 || [];
    chartSma200 = sma200 || [];
  }
  if (!chartPrices.length) return;

  const canvas = document.getElementById('priceChart');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const dpr = window.devicePixelRatio || 1;

  const rect = canvas.parentElement.getBoundingClientRect();
  canvas.width = rect.width * dpr;
  canvas.height = rect.height * dpr;
  canvas.style.width = rect.width + 'px';
  canvas.style.height = rect.height + 'px';
  ctx.scale(dpr, dpr);

  const w = rect.width;
  const h = rect.height;
  const days = chartPrices.length;

  const allVals = [...chartPrices, ...chartSma50.filter(v => v), ...chartSma200.filter(v => v)];
  const minP = Math.min(...allVals) * 0.995;
  const maxP = Math.max(...allVals) * 1.005;
  const padY = 20;

  const scaleX = (i) => (i / (days - 1)) * w;
  const scaleY = (p) => padY + (1 - (p - minP) / (maxP - minP)) * (h - padY * 2);

  // Grid
  ctx.strokeStyle = 'rgba(255,255,255,0.03)';
  ctx.lineWidth = 1;
  for (let i = 0; i < 5; i++) {
    const y = padY + (i / 4) * (h - padY * 2);
    ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(w, y); ctx.stroke();
  }

  // Area fill
  const gradient = ctx.createLinearGradient(0, 0, 0, h);
  gradient.addColorStop(0, 'rgba(0, 212, 170, 0.15)');
  gradient.addColorStop(1, 'rgba(0, 212, 170, 0.0)');
  ctx.beginPath();
  ctx.moveTo(scaleX(0), h);
  chartPrices.forEach((p, i) => ctx.lineTo(scaleX(i), scaleY(p)));
  ctx.lineTo(scaleX(days - 1), h);
  ctx.closePath();
  ctx.fillStyle = gradient;
  ctx.fill();

  // Price line
  ctx.beginPath();
  chartPrices.forEach((p, i) => i === 0 ? ctx.moveTo(scaleX(i), scaleY(p)) : ctx.lineTo(scaleX(i), scaleY(p)));
  ctx.strokeStyle = '#00d4aa';
  ctx.lineWidth = 2;
  ctx.stroke();

  // SMA50 line
  if (chartSma50.length) {
    ctx.beginPath();
    let started = false;
    chartSma50.forEach((p, i) => {
      if (!p) return;
      const x = scaleX(i), y = scaleY(p);
      if (!started) { ctx.moveTo(x, y); started = true; } else ctx.lineTo(x, y);
    });
    ctx.strokeStyle = 'rgba(251, 191, 36, 0.6)';
    ctx.lineWidth = 1.5;
    ctx.setLineDash([4, 4]);
    ctx.stroke();
    ctx.setLineDash([]);
  }

  // SMA200 line
  if (chartSma200.length) {
    ctx.beginPath();
    let started = false;
    chartSma200.forEach((p, i) => {
      if (!p) return;
      const x = scaleX(i), y = scaleY(p);
      if (!started) { ctx.moveTo(x, y); started = true; } else ctx.lineTo(x, y);
    });
    ctx.strokeStyle = 'rgba(167, 139, 250, 0.5)';
    ctx.lineWidth = 1.5;
    ctx.setLineDash([2, 3]);
    ctx.stroke();
    ctx.setLineDash([]);
  }

  // Current price dot
  const lastX = scaleX(days - 1);
  const lastY = scaleY(chartPrices[days - 1]);
  ctx.beginPath(); ctx.arc(lastX, lastY, 4, 0, Math.PI * 2); ctx.fillStyle = '#00d4aa'; ctx.fill();
  ctx.beginPath(); ctx.arc(lastX, lastY, 8, 0, Math.PI * 2); ctx.fillStyle = 'rgba(0, 212, 170, 0.2)'; ctx.fill();

  // Price labels
  ctx.font = '10px JetBrains Mono, monospace';
  ctx.fillStyle = 'rgba(255,255,255,0.3)';
  ctx.textAlign = 'right';
  for (let i = 0; i <= 4; i++) {
    const p = minP + (maxP - minP) * (1 - i / 4);
    const y = padY + (i / 4) * (h - padY * 2);
    ctx.fillText('$' + p.toFixed(1), w - 4, y - 4);
  }
}

// ===== Format helpers =====
function fmtPrice(v) { return '$' + Number(v).toFixed(2); }
function fmtNum(v, d = 2) { return Number(v).toFixed(d); }
function fmtVol(v) {
  v = Math.abs(v);
  if (v >= 1e9) return (v / 1e9).toFixed(2) + 'B';
  if (v >= 1e6) return (v / 1e6).toFixed(1) + 'M';
  if (v >= 1e3) return (v / 1e3).toFixed(0) + 'K';
  return v.toFixed(0);
}
function sigClass(ok) { return ok ? 'buy' : 'sell'; }
function sigText(ok, buyText, sellText) { return ok ? buyText + ' ✅' : sellText + ' ❌'; }
function checkIcon(ok) { return ok ? '✅' : '❌'; }

// ===== Update Dashboard with Real Data =====
function updateDashboard(d) {
  const ind = d.indicators;
  const cond = d.conditions;
  const risk = d.risk;
  const fib = d.fibonacci;
  const regime = d.regime;
  const rs = d.relativeStrength;

  // Top stats
  document.getElementById('tickerName').textContent = d.ticker;
  document.getElementById('currentPrice').textContent = fmtPrice(d.close);
  const changeEl = document.getElementById('priceChange');
  const isUp = d.priceChange >= 0;
  changeEl.className = 'stat-change ' + (isUp ? 'positive' : 'negative');
  changeEl.innerHTML = `
    <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
      <path d="${isUp ? 'M12 4l-8 8h5v8h6v-8h5z' : 'M12 20l8-8h-5V4H9v8H4z'}"/>
    </svg>
    <span>${isUp ? '+' : ''}${d.priceChange} (${isUp ? '+' : ''}${d.priceChangePct}%)</span>
  `;

  document.getElementById('high52w').textContent = fmtPrice(d.high52w);
  document.getElementById('low52w').textContent = fmtPrice(d.low52w);
  const fromATH = ((d.close / d.high52w - 1) * 100).toFixed(1);
  const fromLow = ((d.close / d.low52w - 1) * 100).toFixed(1);
  document.querySelector('.stat-card:nth-child(2) .stat-sub').textContent = `from ATH: ${fromATH}%`;
  document.querySelector('.stat-card:nth-child(3) .stat-sub').textContent = `from Low: +${fromLow}%`;

  // Signal
  const badge = document.getElementById('signalBadge');
  badge.className = 'signal-badge ' + d.signal.toLowerCase();
  const sigIcons = { BUY: '▲', SELL: '▼', HOLD: '■' };
  badge.innerHTML = `<span class="signal-icon">${sigIcons[d.signal]}</span><span>${d.signal}</span>`;
  document.getElementById('trendScore').textContent = d.trendScore;
  document.querySelector('.signal-card').style.borderLeftColor =
    d.signal === 'BUY' ? 'var(--accent-green)' : d.signal === 'SELL' ? 'var(--accent-red)' : 'var(--accent-yellow)';

  // Core indicators
  document.getElementById('sma50').textContent = fmtPrice(ind.sma50);
  document.getElementById('sma200').textContent = fmtPrice(ind.sma200);
  document.getElementById('smaSignal').textContent = cond.goldenCross ? 'Golden Cross ✅' : 'Death Cross ❌';
  document.getElementById('smaSignal').className = 'indicator-signal ' + sigClass(cond.goldenCross);

  document.getElementById('rsiSignal').textContent = ind.rsi > 70 ? `과매수 (${ind.rsi})` : ind.rsi < 30 ? `과매도 (${ind.rsi})` : `중립 (${ind.rsi})`;
  document.getElementById('rsiSignal').className = 'indicator-signal ' + (ind.rsi > 70 ? 'sell' : ind.rsi < 30 ? 'buy' : 'neutral');
  document.getElementById('rsiPointer').style.left = ind.rsi + '%';

  document.getElementById('volSignal').textContent = sigText(cond.volumeOk, `양수 (${ind.volOsc > 0 ? '+' : ''}${ind.volOsc}%)`, `음수 (${ind.volOsc}%)`);
  document.getElementById('volSignal').className = 'indicator-signal ' + sigClass(cond.volumeOk);
  document.getElementById('volFast').textContent = fmtVol(ind.volFast);
  document.getElementById('volSlow').textContent = fmtVol(ind.volSlow);

  // Extended indicators
  document.getElementById('macdSignal').className = 'indicator-signal ' + sigClass(cond.macdBullish);
  document.getElementById('macdSignal').textContent = sigText(cond.macdBullish, 'Bullish', 'Bearish');
  document.getElementById('macdLine').textContent = fmtNum(ind.macd, 4);
  document.getElementById('macdSignalLine').textContent = fmtNum(ind.macdSignal, 4);
  const histEl = document.getElementById('macdHist');
  histEl.textContent = (ind.macdHist >= 0 ? '+' : '') + fmtNum(ind.macdHist, 4);
  histEl.className = 'ind-val-num ' + (ind.macdHist >= 0 ? 'positive' : 'negative');

  document.getElementById('bbSignal').textContent = sigText(cond.bbNotUpper, `밴드 내 (${(ind.bbPband * 100).toFixed(0)}%)`, `상단밴드 (${(ind.bbPband * 100).toFixed(0)}%)`);
  document.getElementById('bbSignal').className = 'indicator-signal ' + sigClass(cond.bbNotUpper);
  document.getElementById('bbUpper').textContent = fmtPrice(ind.bbUpper);
  document.getElementById('bbMiddle').textContent = fmtPrice(ind.bbMiddle);
  document.getElementById('bbLower').textContent = fmtPrice(ind.bbLower);
  document.getElementById('bbMarker').style.bottom = Math.min(100, Math.max(0, ind.bbPband * 100)) + '%';

  document.getElementById('stochSignal').textContent = sigText(cond.stochNotOver, '매수 적합', '과매수');
  document.getElementById('stochSignal').className = 'indicator-signal ' + sigClass(cond.stochNotOver);
  document.getElementById('stochK').textContent = fmtNum(ind.stochK);
  document.getElementById('stochD').textContent = fmtNum(ind.stochD);
  document.getElementById('stochPointer').style.left = Math.min(100, ind.stochK) + '%';

  // Advanced indicators
  document.getElementById('adxSignal').textContent = sigText(cond.adxTrending, '강한 추세', '약한 추세');
  document.getElementById('adxSignal').className = 'indicator-signal ' + sigClass(cond.adxTrending);
  document.getElementById('adxValue').textContent = fmtNum(ind.adx, 1);
  document.getElementById('adxValue').style.color = cond.adxTrending ? 'var(--accent-green)' : 'var(--accent-yellow)';
  document.getElementById('adxFill').style.width = Math.min(100, ind.adx) + '%';

  document.getElementById('mfiSignal').textContent = sigText(cond.mfiOk, `정상 (${fmtNum(ind.mfi, 1)})`, `과매수 (${fmtNum(ind.mfi, 1)})`);
  document.getElementById('mfiSignal').className = 'indicator-signal ' + sigClass(cond.mfiOk);
  document.getElementById('mfiPointer').style.left = Math.min(100, ind.mfi) + '%';

  document.getElementById('obvSignal').textContent = sigText(cond.obvRising, '상승 추세', '하락 추세');
  document.getElementById('obvSignal').className = 'indicator-signal ' + sigClass(cond.obvRising);
  document.getElementById('obvValue').textContent = fmtVol(ind.obv);
  document.getElementById('obvSma').textContent = fmtVol(ind.obvSma);

  // Market Regime
  if (regime) {
    const regimeMap = {
      'NORMAL': { emoji: '🟢', cls: 'normal', desc: 'VIX 15~25 구간, 정상적 변동성' },
      'LOW_VOL': { emoji: '🔵', cls: 'low-vol', desc: 'VIX < 15, 낮은 변동성' },
      'HIGH_VOL': { emoji: '🟠', cls: 'high-vol', desc: 'VIX 25~35, 높은 변동성 주의' },
      'EXTREME_FEAR': { emoji: '🔴', cls: 'extreme-fear', desc: 'VIX > 35, 극단적 공포' },
    };
    const rm = regimeMap[regime.regime] || regimeMap['NORMAL'];
    const box = document.getElementById('regimeBox');
    box.className = 'regime-box ' + rm.cls;
    box.querySelector('.regime-emoji').textContent = rm.emoji;
    document.getElementById('regimeName').textContent = regime.regime;
    box.querySelector('.regime-desc').textContent = rm.desc;
    document.getElementById('vixValue').textContent = fmtNum(regime.vix);
    const trendEmoji = regime.spyTrend === 'BULL' ? 'BULL 🐂' : regime.spyTrend === 'BEAR' ? 'BEAR 🐻' : 'SIDEWAYS ➡️';
    document.getElementById('spyTrend').textContent = trendEmoji;
    document.getElementById('spyTrend').className = 'detail-value ' + (regime.spyTrend === 'BULL' ? 'positive' : regime.spyTrend === 'BEAR' ? 'negative' : '');
    document.getElementById('spySma50').textContent = fmtPrice(regime.spySma50);
    document.getElementById('spySma200').textContent = fmtPrice(regime.spySma200);
  }

  // Risk management
  document.getElementById('tpPrice').textContent = fmtPrice(risk.takeProfit);
  document.getElementById('riskCurrentPrice').textContent = fmtPrice(d.close);
  document.getElementById('slPrice').textContent = fmtPrice(risk.stopLoss);
  const tpPct = ((risk.takeProfit / d.close - 1) * 100).toFixed(1);
  const slPct = ((risk.stopLoss / d.close - 1) * 100).toFixed(1);
  document.querySelector('.risk-level.tp .risk-pct').textContent = '+' + tpPct + '%';
  document.querySelector('.risk-level.sl .risk-pct').textContent = slPct + '%';
  document.getElementById('atrValue').textContent = fmtPrice(ind.atr);
  document.getElementById('rrRatio').textContent = '1:' + fmtNum(risk.riskReward, 1);
  document.getElementById('kellyPct').textContent = risk.kellyPct + '%';

  // Fibonacci
  if (fib) {
    document.getElementById('fib0').textContent = fmtPrice(fib.high);
    document.getElementById('fib236').textContent = fmtPrice(fib.level_236);
    document.getElementById('fib382').textContent = fmtPrice(fib.level_382);
    document.getElementById('fib50').textContent = fmtPrice(fib.level_500);
    document.getElementById('fib618').textContent = fmtPrice(fib.level_618);
    document.getElementById('fib786').textContent = fmtPrice(fib.level_786);
    document.getElementById('fib100').textContent = fmtPrice(fib.low);
  }

  // Relative Strength
  if (rs) {
    document.querySelectorAll('[id^="rsTicker"]').forEach(el => {
      if (!el.id.includes('Bar') && !el.id.includes('Pct')) el.textContent = d.ticker;
    });
    const maxRet = Math.max(Math.abs(rs.tickerReturn1m), Math.abs(rs.spyReturn1m), Math.abs(rs.tickerReturn3m), Math.abs(rs.spyReturn3m), 1);
    document.getElementById('rsTickerBar1m').style.width = Math.abs(rs.tickerReturn1m) / maxRet * 100 + '%';
    document.getElementById('rsSpyBar1m').style.width = Math.abs(rs.spyReturn1m) / maxRet * 100 + '%';
    document.getElementById('rsTickerPct1m').textContent = (rs.tickerReturn1m >= 0 ? '+' : '') + rs.tickerReturn1m + '%';
    document.getElementById('rsTickerPct1m').className = 'rs-pct ' + (rs.tickerReturn1m >= 0 ? 'positive' : 'negative');
    document.getElementById('rsSpyPct1m').textContent = (rs.spyReturn1m >= 0 ? '+' : '') + rs.spyReturn1m + '%';

    document.getElementById('rsTickerBar3m').style.width = Math.abs(rs.tickerReturn3m) / maxRet * 100 + '%';
    document.getElementById('rsSpyBar3m').style.width = Math.abs(rs.spyReturn3m) / maxRet * 100 + '%';
    document.getElementById('rsTickerPct3m').textContent = (rs.tickerReturn3m >= 0 ? '+' : '') + rs.tickerReturn3m + '%';
    document.getElementById('rsTickerPct3m').className = 'rs-pct ' + (rs.tickerReturn3m >= 0 ? 'positive' : 'negative');
    document.getElementById('rsSpyPct3m').textContent = (rs.spyReturn3m >= 0 ? '+' : '') + rs.spyReturn3m + '%';

    const verdict = document.getElementById('rsVerdict');
    verdict.textContent = rs.outperforming ? '✅ SPY 대비 아웃퍼폼 중' : '❌ SPY 대비 언더퍼폼';
    verdict.className = 'rs-verdict ' + (rs.outperforming ? 'positive' : 'negative');
  }

  // Sentiment / News
  if (d.news && d.news.length) {
    const newsList = document.getElementById('newsList');
    newsList.innerHTML = d.news.map(n => `
      <div class="news-item">
        <div class="news-sentiment neutral-sent">N/A</div>
        <div class="news-text">
          <div class="news-title">${n.title}</div>
          <div class="news-meta">${n.source} • ${n.published || ''}</div>
        </div>
      </div>
    `).join('');
    document.getElementById('sentimentScore').textContent = 'N/A';
    document.querySelector('.sentiment-label').textContent = 'No LLM';
  }

  // Signal summary
  const summaryMap = {
    sumSma: [cond.goldenCross, 'SMA Golden Cross'],
    sumRsi: [cond.rsiOk, 'RSI 정상 범위'],
    sumVol: [cond.volumeOk, '거래량 확인'],
    sumMacd: [cond.macdBullish, 'MACD Bullish'],
    sumBb: [cond.bbNotUpper, '볼린저 밴드 내'],
    sumStoch: [cond.stochNotOver, '스토캐스틱 적합'],
    sumAdx: [cond.adxTrending, 'ADX 강한 추세'],
    sumMfi: [cond.mfiOk, 'MFI 정상'],
    sumObv: [cond.obvRising, 'OBV 상승'],
  };
  for (const [id, [ok, text]] of Object.entries(summaryMap)) {
    const el = document.getElementById(id);
    el.className = 'signal-check ' + sigClass(ok);
    el.innerHTML = `<span class="check-icon">${checkIcon(ok)}</span> ${text}`;
  }
  document.getElementById('sumSentiment').className = 'signal-check neutral-sig';
  document.getElementById('sumSentiment').innerHTML = '<span class="check-icon">➖</span> 감성 (LLM 미연결)';
  const regimeOk = regime && (regime.regime === 'NORMAL' || regime.regime === 'LOW_VOL');
  document.getElementById('sumRegime').className = 'signal-check ' + sigClass(regimeOk);
  document.getElementById('sumRegime').innerHTML = `<span class="check-icon">${checkIcon(regimeOk)}</span> 시장 레짐 ${regimeOk ? '정상' : '주의'}`;
  const rsOk = rs && rs.outperforming;
  document.getElementById('sumRs').className = 'signal-check ' + sigClass(rsOk);
  document.getElementById('sumRs').innerHTML = `<span class="check-icon">${checkIcon(rsOk)}</span> 상대강도 ${rsOk ? '우위' : '열세'}`;

  // Chart
  if (d.chartData && d.chartData.length) {
    drawChart(
      d.chartData.map(c => c.close),
      d.chartData.map(c => c.sma50),
      d.chartData.map(c => c.sma200)
    );
  }
}

// ===== Analyze button =====
const analyzeBtn = document.getElementById('analyzeBtn');
const tickerInput = document.getElementById('tickerInput');

async function runAnalysis() {
  const ticker = tickerInput.value.trim().toUpperCase();
  if (!ticker) return;

  document.getElementById('tickerName').textContent = ticker;
  analyzeBtn.innerHTML = '<span>분석 중...</span>';
  analyzeBtn.disabled = true;

  try {
    const resp = await fetch(`${API_BASE}/api/analyze/${ticker}`);
    if (!resp.ok) {
      const err = await resp.json();
      alert(`분석 실패: ${err.detail || resp.statusText}`);
      return;
    }
    const data = await resp.json();
    updateDashboard(data);
  } catch (e) {
    alert(`서버 연결 실패: ${e.message}\n\nAPI 서버가 실행 중인지 확인하세요:\npython3 api_server.py`);
  } finally {
    analyzeBtn.innerHTML = '<span>분석</span><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>';
    analyzeBtn.disabled = false;
  }
}

analyzeBtn.addEventListener('click', runAnalysis);
tickerInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') runAnalysis();
});

// ===== Timeframe buttons =====
document.querySelectorAll('.tf-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.tf-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    drawChart();
  });
});

// ===== Market Status =====
function updateMarketStatus() {
  const now = new Date();
  const ny = new Date(now.toLocaleString('en-US', { timeZone: 'America/New_York' }));
  const day = ny.getDay();
  const hour = ny.getHours();
  const min = ny.getMinutes();
  const time = hour * 60 + min;
  const isOpen = day >= 1 && day <= 5 && time >= 570 && time < 960;
  const statusEl = document.getElementById('marketStatus');
  if (isOpen) {
    statusEl.classList.add('open');
    statusEl.querySelector('span:last-child').textContent = 'Market Open';
  } else {
    statusEl.classList.remove('open');
    statusEl.querySelector('span:last-child').textContent = 'Market Closed';
  }
}

// ===== Init =====
window.addEventListener('load', () => {
  updateMarketStatus();
  setInterval(updateMarketStatus, 60000);
});
window.addEventListener('resize', () => drawChart());
