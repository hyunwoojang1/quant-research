# 📚 사전 지식 정리 — BDA 논문 (Transformer DRL + Black-Litterman)

> 대상 논문: Sun et al., *Combining Transformer based Deep Reinforcement Learning with the
> Black-Litterman Model for Portfolio Optimization*, 2024 (arXiv 2402.16609)
>
> 이 문서는 논문을 **혼자 깊이 읽기 위해 미리 갖춰야 할 지식**을 모은 학습 가이드입니다.
> 각 항목: **무엇 / 왜 이 논문에 필요 / 핵심 / 더 볼 자료**.

---

## 0. 추천 학습 순서 (위에서 아래로)

1. 포트폴리오 금융 기초 (수익률, 공분산, Markowitz, Sharpe/Sortino, 롱숏·레버리지·거래비용)
2. **Black-Litterman(BL) 모델** (prior/equilibrium, view, 사후분포) ⭐
3. 최적화 (이차계획 QP, 라그랑주, 역최적화/implied returns)
4. **강화학습(RL)** 기초 (MDP, 정책/가치, 정책경사, DPG/actor-critic, 차원의 저주) ⭐
5. 딥러닝 (신경망, CNN, **Transformer & self-attention**, 위치인코딩)
6. 베이지안 기초 (prior/posterior, 조건부 정규분포)
7. 평가지표 정의 (AR, DR, Std, LStd, SR, STR)

> 이 논문의 두 기둥은 **BL 모델(2번)** 과 **정책경사 RL(4번)** 입니다. 둘을 먼저 잡으세요.

---

## 1. 포트폴리오 금융 기초

- [ ] **로그수익률** `r_{i,t} = log₂(c_{i,t}/c_{i,t−1})` — 논문이 쓰는 수익률 정의.
- [ ] **기대수익 벡터 μ, 공분산 행렬 Σ** — BL과 평균-분산의 입력.
- [ ] **Markowitz 평균-분산 최적화**와 그 약점 **error maximization**
  - 왜 필요: BL이 등장한 이유(추정오차가 큰 자산을 과대편입 → OOS 악화)를 이해하려면 필수.
- [ ] **Sharpe(SR) / Sortino(STR)** — 위험 대비 수익. STR은 하방위험(LStd)만 사용.
- [ ] **롱/숏(공매도), 레버리지, 거래비용·차입비용, 무위험금리**
  - 왜 필요: 논문은 공매도 허용, 총투자=초기자본의 0.5배(레버리지 제한),
    수수료·차입비용 반영, 무위험금리=0 가정.
- 더 볼 자료: Markowitz(1952) 개요, Sharpe/Sortino 정의 정리.

---

## 2. Black-Litterman(BL) 모델 ⭐(핵심)

> BL은 "시장균형(prior)"과 "투자자 view"를 베이지안으로 결합해 사후 기대수익을 만드는 모델.

- [ ] **prior = 균형(equilibrium) 기대수익 Π**
  - 핵심: **역최적화(reverse/implied optimization)** 로 도출. "각 자산이 동일 투자가치를 가진다"는
    중립 가정에서 시장이 함의하는 기대수익을 역산(논문 식 11).
- [ ] **view (투자자 의견)**: 선형식으로 표현. `P·μ = Q + ε`, `ε~N(0, Ω)`.
  - 핵심 용어: **view 행렬 P**(어떤 자산에 대한 의견인지), **Q**(의견의 기대값), **Ω**(의견의 불확실성).
  - 논문 특화: DRL이 모든 자산에 절대 view를 주므로 **P = 항등행렬 I**, `Ω=diag(τ·PΣP')`.
- [ ] **사후분포(posterior)**: prior와 view를 신뢰도로 가중 결합 → μ_post, Σ_post (논문 식 13).
  - 핵심: 신뢰도(τ, Ω)에 따라 시장균형과 내 의견 사이에서 균형점을 찾음.
- 더 볼 자료: Black & Litterman(1992); He & Litterman, *The Intuition Behind BL Model Portfolios*(가장 추천).

---

## 3. 최적화 (Optimization)

- [ ] **이차계획법(Quadratic Programming, QP)** — 평균-분산/BL의 가중치 산출이 QP.
- [ ] **라그랑주 승수법(등식 제약)** — `wᵀ1=1` 같은 제약 하의 해.
  - 논문 식 15: `w = (1/λ)·Σ_post⁻¹·μ_post` (오목 QP의 폐형 해).
- [ ] **역최적화(implied/reverse optimization)** — 균형수익 Π를 가중치에서 역산(2번과 연결).
- 더 볼 자료: convex optimization 입문의 QP·라그랑주 부분.

---

## 4. 강화학습(RL) ⭐(핵심)

- [ ] **마르코프 결정과정(MDP)**: 상태 s, 행동 a, 보상 R, 정책 π. 포트폴리오를 MDP로 정식화.
  - 논문: 상태 `sₜ=(w_{t−1}, Xₜ)`, 행동 `aₜ=wₜ`(포트폴리오 비중), 보상 R(아래 6번).
- [ ] **가치기반 vs 정책기반** — 논문은 **정책기반(policy-only)**.
- [ ] **정책경사(Policy Gradient) / 결정론적 정책(DPG)**
  - 핵심: 정책을 직접 파라미터화하고 목적함수 기울기로 갱신. 결정론적 정책은 상태→행동을 확정 매핑.
- [ ] **Actor-Critic & 그 한계(차원의 저주)**
  - 왜 필요: 논문이 **critic을 쓰지 않는 이유**. 고차원 연속 행동공간에서 critic 학습이 불안정 →
    보상함수로 **미분가능 목적함수**를 만들어 해석적 기울기를 정책망에 직접 역전파.
- [ ] **EIIE 토폴로지 (Jiang et al.)** — 자산별 동일 평가기를 공유하는 포트폴리오 정책 구조.
- 더 볼 자료: Sutton & Barto, *Reinforcement Learning*(MDP/정책경사); Silver et al., *DPG*(2014);
  Jiang et al., *A Deep RL Framework for the Financial Portfolio Management Problem*(2017, EIIE).

---

## 5. 딥러닝 (신경망 구성요소)

- [ ] **신경망·역전파**, **CNN** — τ2(위험회피 출력)가 CNN.
- [ ] **Transformer & self-attention** ⭐
  - 왜 필요: τ1(view 출력)이 Transformer. 여러 자산 수익률 시계열의 **비선형 상관**을 포착.
  - 핵심: self-attention이 시퀀스 요소 간 관계를 병렬로 학습.
- [ ] **위치인코딩(positional encoding)과 "왜 제거했나"**
  - 논문은 위치인코딩을 **제거** → 시점 순서 과적합을 막고 자산 간 관계 학습에 집중.
    (입력을 5일 단위 패치 시퀀스로 분해해 처리)
- 더 볼 자료: Vaswani et al., *Attention Is All You Need*(2017).

---

## 6. 베이지안 & 보상함수 이해

- [ ] **prior/posterior, 조건부 정규분포** `r|μ ~ N(μ, Σ)` — BL의 베이지안 골격.
- [ ] **보상함수 읽기**: `R = (1/5)·μ_p − (z1/2)·σ_p² − z2·χ_p`
  - 의미: 일평균수익 − 분산패널티 − 거래규모패널티. z1, z2는 양의 상수.
  - 학습목표: 누적보상 ARD 최대화(논문 식 18).
- 더 볼 자료: 베이지안 추론 입문(정규-정규 켤레).

---

## 7. 평가지표 정의 (결과 해석용)

- [ ] **AR**(누적수익), **DR**(일수익), **Std**(표준편차), **LStd**(하방 표준편차),
      **SR**(Sharpe), **STR**(Sortino).
- 왜 필요: 결과표(BDA vs CRP/ONS/UP 등)를 해석하려면 각 지표의 의미를 알아야 함.

---

## ✅ 최종 체크리스트 (이걸 다 알면 논문이 술술 읽힘)

- [ ] Markowitz의 error maximization 문제와 BL이 그것을 어떻게 푸는지 설명 가능
- [ ] BL의 prior(균형수익)·view(P,Q,Ω)·posterior 결합을 식으로 이해
- [ ] 역최적화로 균형수익 Π를 구하는 개념 이해
- [ ] MDP로 포트폴리오를 정식화(s,a,R)할 수 있음
- [ ] 정책경사·결정론적 정책, actor-critic의 차원의 저주, critic 제거 이유 이해
- [ ] self-attention과 "위치인코딩 제거" 의도 이해
- [ ] 보상함수 `R=(1/5)μ_p−(z1/2)σ_p²−z2χ_p`를 항별로 해석 가능
- [ ] AR·SR·STR로 결과를 해석할 수 있음

---

### 한 줄 지도
**"DRL이 직접 가중치를 정하는 대신, BL 모델에 넣을 'view와 위험회피'만 학습한다.
Transformer가 자산 간 상관을 읽어 view를 만들고, BL이 안정적으로 가중치를 산출한다."**
— BL(2번)과 정책경사 RL(4번)만 잡으면 논문의 80%를 이해한 것.
