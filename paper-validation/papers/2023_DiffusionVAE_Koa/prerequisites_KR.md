# 📚 사전 지식 정리 — D-Va 논문 (Diffusion-VAE 주가 예측)

> 대상 논문: Koa et al., *Diffusion Variational Autoencoder for Tackling Stochasticity in
> Multi-Step Regression Stock Price Prediction*, CIKM 2023 (arXiv 2309.00073)
>
> 이 문서는 논문을 **혼자 깊이 읽기 위해 미리 갖춰야 할 지식**을 모은 학습 가이드입니다.
> 각 항목: **무엇 / 왜 이 논문에 필요 / 핵심 / 더 볼 자료**.

---

## 0. 추천 학습 순서 (위에서 아래로)

1. 확률·통계 기초 (정규분포, 조건부분포, KL divergence, 베이즈)
2. 금융 시계열 기초 (수익률, 변동성, OHLCV, Sharpe, Markowitz)
3. 딥러닝 기초 (신경망, 역전파, CNN, 손실함수)
4. 오토인코더 → **VAE** → **계층적 VAE(NVAE)**
5. **확산모델(DDPM)** → 스코어매칭 → **디노이징 스코어매칭(DSM)**
6. 불확실성 개념 (aleatoric vs epistemic)
7. 포트폴리오 응용 (평균-분산 최적화, graphical lasso)
8. 비교 베이스라인 개념 (ARIMA, LSTM+Attention, Autoformer)

> 시간이 없다면 **4, 5번(VAE·확산)** 이 이 논문의 심장입니다. 여기에 집중하세요.

---

## 1. 확률·통계 기초

- [ ] **정규분포 N(μ, σ²)와 다변량 정규분포**
  - 왜 필요: 확산과정·잠재변수가 모두 가우시안으로 정의됨 (예: `q(Xₙ|X)=N(Xₙ; √ᾱₙX, (1−ᾱₙ)I)`).
  - 핵심: 평균/분산, 공분산 행렬 Σ, 항등행렬 I.
- [ ] **조건부분포 / 결합분포**
  - 왜 필요: 예측밀도 `p(ŷₙ|Xₙ)`, 마르코프 연쇄 `q(X₁:ₙ|X)=∏ q(Xₙ|Xₙ₋₁)`.
- [ ] **KL divergence (쿨백-라이블러 발산)** `D_KL(p‖q)`
  - 왜 필요: VAE의 정규화 항과 타깃 결합확산의 손실 `L_KL = D_KL(p(ŷₙ)‖q(yₙ))`의 핵심.
  - 핵심: 두 분포가 얼마나 다른지 측정(0이면 동일, 비대칭).
- [ ] **베이즈 정리 / 사후분포 개념** — VAE의 잠재변수 추론(인코더=근사 사후분포)을 이해하는 토대.
- [ ] **기대값·분산·공분산, 표준편차** — 결과 지표(MSE의 SD, 포트폴리오 공분산)에 필요.
- 더 볼 자료: 임의의 "확률과 통계" 입문 + KL divergence 시각 설명(블로그/유튜브).

---

## 2. 금융 시계열 기초

- [ ] **수익률**: 퍼센트수익률 `rₜ = cₜ/cₜ₋₁`, 절대수익 `Δₜ = cₜ − cₜ₋₁` (논문 입력 피처).
- [ ] **OHLCV**: open/high/low/close/volume — 입력 6피처 `xₜ=[o,h,l,v,Δ,r]`의 구성요소.
  - 핵심 전처리: o/h/l을 **전일 종가로 정규화**(`oₜ←oₜ/cₜ₋₁`)하는 이유(스케일 제거).
- [ ] **변동성(volatility)** — 멀티스텝 예측의 동기(파생상품 헤지·위험관리).
- [ ] **Sharpe ratio** `SR = 평균초과수익 / 수익표준편차` — 포트폴리오 성과 비교지표.
- [ ] **Markowitz 평균-분산 최적화** `max_w wᵀμ − (γ/2)wᵀΣw, s.t. wᵀ1=1`
  - 왜 필요: 예측 결과로 포트폴리오를 구성하는 RQ3 부분.
  - 핵심: 기대수익 μ, 공분산 Σ, 위험회피 γ, 무공매도 제약 w≥0.
- 더 볼 자료: Markowitz 포트폴리오 이론 입문.

---

## 3. 딥러닝 기초

- [ ] **신경망·역전파·경사하강(Adam optimizer)** — 학습 방식(lr 5e-4, 배치 16).
- [ ] **합성곱 신경망(CNN)** — VAE residual cell이 conv 기반.
- [ ] **Batch Normalization, 활성화함수(Swish `f(x)=x·σ(x)`)** — NVAE 셀 구성요소.
- [ ] **Squeeze-and-Excitation(SE) 블록** — 채널 간 상호의존을 모델링하는 게이팅(셀에 사용).
- [ ] **Depthwise Separable Convolution** — 연산량을 줄이며 수용영역 확대(디코더 셀).
- [ ] **MSE 손실** — 예측-정답 오차(주 평가지표).
- 더 볼 자료: CNN 구성요소 개념 정리, SE-Net / depthwise conv 그림 설명.

---

## 4. 오토인코더 → VAE → 계층적 VAE ⭐(핵심)

- [ ] **오토인코더(AE)**: 입력을 압축(인코더)했다 복원(디코더)하는 신경망.
- [ ] **변분오토인코더(VAE)**: 잠재변수 z를 **확률분포**로 인코딩하는 생성모델.
  - 왜 필요: D-Va의 백본. "확률적 생성과정"이라는 논문 프레임의 출발점.
  - 핵심 개념: **ELBO(증거하한)**, **reparameterization trick**(`z=μ+σ·ε`로 미분가능 샘플링),
    손실 = 재구성오차 + KL(q(z|x)‖p(z)).
- [ ] **계층적 VAE / NVAE**: 잠재변수를 여러 층 `Z={Z1,Z2,Z3}`으로 쌓아 표현력 강화.
  - 왜 필요: 단일 잠재변수보다 주가의 복잡·저수준 패턴을 더 잘 포착(논문이 NVAE를 seq2seq로 전용).
- 더 볼 자료: Kingma & Welling, *Auto-Encoding Variational Bayes*(2013, 원 VAE);
  Vahdat & Kautz, *NVAE*(2020).

---

## 5. 확산모델 → 스코어매칭 → DSM ⭐(핵심)

- [ ] **확산 정과정(forward)**: 데이터에 가우시안 노이즈를 단계적으로 추가.
  - 핵심 식: `Xₙ = √ᾱₙ·X + √(1−ᾱₙ)·ε`, 분산 스케줄 `βₙ`, `ᾱₙ=∏(1−βᵢ)`.
  - 트릭: **reparameterization**으로 임의 단계 n을 한 번에 샘플(반복 샘플 불필요).
- [ ] **확산 역과정(reverse) / DDPM**: 노이즈에서 데이터를 복원하도록 학습.
  - 왜 필요: 논문은 입력(X-Diffusion)과 타깃(Y-Diffusion)에 노이즈를 주입해 확률성 모사.
- [ ] **스코어매칭 / 디노이징 스코어매칭(DSM)**:
  - 핵심: 노이즈 샘플 ŷₙ에서 깨끗한 데이터로 향하는 기울기(스코어) `∇E(ŷ)`를 학습.
  - 테스트 시 **1-step 디노이징 점프** `ŷ_final = ŷ − ∇E(ŷ)`로 잡음 제거.
  - 손실: `L_DSM,n = E[ σₙ·‖ y − ŷₙ + ∇E(ŷₙ) ‖² ]`.
- 더 볼 자료: Ho et al., *DDPM*(2020); Song & Ermon, *score-based generative models*;
  "결합확산(coupled diffusion)으로 불확실성 감소"를 다룬 선행연구(논문 식 4 참고).

---

## 6. 불확실성 개념

- [ ] **Aleatoric(데이터 고유 잡음)** vs **Epistemic(모델·추정 불확실성)**
  - 왜 필요: 논문 설계 철학. 확산+디노이징=aleatoric 처리, graphical lasso=epistemic 처리.
- 더 볼 자료: Kendall & Gal, *What Uncertainties Do We Need...*(2017).

---

## 7. 포트폴리오 응용 (RQ3)

- [ ] **평균-분산 최적화 + 무공매도 제약** (1번·2번에서 다룸).
- [ ] **Graphical Lasso (공분산 정규화)** `max_Θ log detΘ − tr(ΣΘ) − λ‖Θ‖₁` (λ=0.1)
  - 왜 필요: 예측 공분산의 불확실성(epistemic)을 L1 규제로 축소(공분산 수축과 유사).
- [ ] **동일가중(equal-weight) 포트폴리오** — 강력한 비교 베이스라인.
- 더 볼 자료: graphical lasso(Friedman et al.), Ledoit-Wolf 공분산 수축.

---

## 8. 비교 베이스라인 개념 (가볍게)

- [ ] **ARIMA** — 전통 통계 시계열(자기회귀+차분+이동평균).
- [ ] **LSTM + Attention (NBA)** — 순환신경망 기반 시계열 예측.
- [ ] **Autoformer** — Transformer 계열 장기예측(분해+자기상관). 가장 강력한 딥러닝 베이스라인.
- 더 볼 자료: Autoformer(Wu et al., 2021).

---

## ✅ 최종 체크리스트 (이걸 다 알면 논문이 술술 읽힘)

- [ ] 정규분포·조건부분포·KL divergence를 식으로 이해
- [ ] VAE의 ELBO·reparameterization·KL 항을 설명할 수 있음
- [ ] 계층적 잠재변수(NVAE)가 왜 표현력이 좋은지 이해
- [ ] 확산 정/역과정과 `Xₙ=√ᾱₙX+√(1−ᾱₙ)ε`를 이해
- [ ] 디노이징 스코어매칭과 1-step 점프 `ŷ−∇E(ŷ)`의 의미 이해
- [ ] aleatoric vs epistemic 불확실성 구분
- [ ] Markowitz 최적화 + graphical lasso로 포트폴리오 구성 흐름 이해
- [ ] MSE·표준편차·Sharpe로 결과를 해석할 수 있음

---

### 한 줄 지도
**"VAE로 핵심을 확률적으로 압축하고, 확산으로 잡음을 일부러 다뤄 강건하게 만들고,
디노이징으로 마지막에 정제한다"** — 이 세 축(2·4·5번)만 잡으면 논문의 80%를 이해한 것.
