# Decision Granularity, Time Discretization and Decision Timing in Sequential Decision Making

Scope: how the choice of *when* decisions are made (fixed time step, event-aligned, learned/adaptive timing) affects learnability, sample efficiency, bias/variance and offline evaluation, across RL, control, optimal stopping, early classification, predictive maintenance and prescriptive process monitoring (PresPM). Written for the KU Leuven thesis on PresPM with IoT-enriched event logs (use case: when to start/stop a cotton-candy spinning step from a sensor stream). Research date: 2026-10-31.

**Verification legend**
- **[V]** = verified in this session (paper page / abstract fetched or surfaced by search with matching metadata).
- **[S]** = secondhand: from the researcher's prior knowledge of the literature; the link is the canonical arXiv/DOI/JMLR identifier as remembered but was NOT re-opened in this session. The report writer should spot-check [S] links before final publication. Where I was unsure of an identifier I used a Semantic Scholar search link instead of guessing.

---

## Q1. RL time discretization: what happens to value-based and policy-gradient RL as the time step shrinks, and how do action repetition / frame-skip / learned action durations help?

### Takeaway
There is a well-established result that standard discrete-time RL breaks down as the decision step dt goes to 0: Q-values collapse onto V (the advantage scales with dt), random exploration averages out, and policy-gradient variance blows up. Remedies are (a) dt-invariant reparametrisations (advantage updating, rescaled discount, SAR) and (b) letting the agent commit to an action for several steps (frame-skip, FiGAR, TempoRL, action persistence, elastic/variable time steps). The latter turns "decision granularity" into something the agent can learn.

### Cited Findings (annotated list)

**Foundational, continuous-time view**
- **Doya (2000), "Reinforcement Learning in Continuous Time and Space", *Neural Computation* 12(1).** Derives continuous-time TD (HJB-based) value learning and advantage-style actor-critic, and shows how discount and TD error must be written in terms of a time constant τ instead of a per-step γ. Relevance: the reference for writing the cotton-candy problem in continuous time, where decision points are sensor ticks, without baking in a step size. [S] — [DOI 10.1162/089976600300015961](https://doi.org/10.1162/089976600300015961)
- **Baird (1994), "Reinforcement learning in continuous time: Advantage updating", ICNN.** First to observe that Q-learning fails as dt→0 because Q(s,a) − V(s) = O(dt), and proposes learning a rescaled advantage A/dt. Relevance: the mechanism behind every later "time-discretization robustness" paper. [S] — [Semantic Scholar search](https://www.semanticscholar.org/search?q=Reinforcement%20learning%20in%20continuous%20time%3A%20advantage%20updating)
- **Munos (2006), "Policy Gradient in Continuous Time", *JMLR* 7.** Analyses policy-gradient estimation for continuous-time deterministic and stochastic systems. It shows that naive likelihood-ratio estimators degrade as the time step shrinks and proposes pathwise alternatives. Relevance: theory for why REINFORCE-style learning from 1 Hz vs 100 Hz sensor data behaves differently. [S] — [JMLR](https://jmlr.org/papers/v7/munos06b.html)
- **Wang, Zariphopoulou & Zhou (2020), "Reinforcement Learning in Continuous Time and Space: A Stochastic Control Approach", *JMLR* 21.** Entropy-regularised "exploratory" continuous-time control. The optimal exploration distribution is Gaussian in the LQ case, which gives a principled exploration formulation that does not depend on dt. [S] — [arXiv 1812.01552](https://arxiv.org/abs/1812.01552)
- **Jia & Zhou (2023), "q-Learning in Continuous Time", *JMLR* 24.** Defines a "little q" function, the first-order (in dt) continuous-time analogue of the Q-function, which stays informative as dt→0, and gives martingale-based q-learning algorithms. Relevance: the cleanest theoretical answer to "how to learn Q at arbitrary times". [S] — [arXiv 2207.00713](https://arxiv.org/abs/2207.00713)

**dt-robust deep RL**
- **Tallec, Blier & Ollivier (2019), "Making Deep Q-learning Methods Robust to Time Discretization", ICML.** Proves that Q-learning (DQN/DDPG) degenerates as dt→0, since there is no continuous-time Q-function. It proposes Deep Advantage Updating (DAU) with dt-rescaled advantages, discount γ = exp(−dt/τ) and temporally-coherent exploration, and shows invariance across frame rates. Relevance: the key reference showing that finer granularity does not come for free. Without reparametrisation, a policy learned on sensor-tick decisions can be worse than one learned on event-aligned decisions. [S] — [arXiv 1901.09732](https://arxiv.org/abs/1901.09732)
- **Park, Kim & Kim (2021), "Time Discretization-Invariant Safe Action Repetition for Policy Gradient Methods", NeurIPS.** Shows that policy-gradient variance diverges as dt→0. Proposes Safe Action Repetition (SAR): the agent repeats an action until the state leaves a learned "safe region", which makes performance roughly invariant to dt. Relevance: state-triggered (not clock-triggered) repetition, structurally the same as deciding at sensor events only when the state has moved enough. [S] — [arXiv 2111.03941](https://arxiv.org/abs/2111.03941)
- **Zhang, Kirschner, Zhang, Zanini, Ayoub, Dehghan & Schuurmans (2023), "Managing Temporal Resolution in Continuous Value Estimation: A Fundamental Trade-off", NeurIPS 2023.** For Monte-Carlo policy evaluation on LQR, finer time resolution lowers approximation (discretization) error but raises statistical error under a fixed data budget, so an optimal step size exists for each budget. The trade-off is confirmed on nonlinear continuous-control benchmarks. Relevance: **the most direct theoretical anchor for the thesis's "granularity-vs-learnability" hypothesis**, and it explicitly treats the time step as a tunable design parameter. [V] — [arXiv 2212.08949](https://arxiv.org/abs/2212.08949)

**Action repetition / frame-skip / learned durations**
- **Lakshminarayanan, Sharma & Ravindran (2017), "Dynamic Action Repetition for Deep RL" (arXiv title "Dynamic Frame skip Deep Q Network"), AAAI.** Adds repeat-count variants of each action to the DQN action space so the agent picks a short or long repetition. Better Atari scores than a fixed frame-skip. [S] — [arXiv 1605.05365](https://arxiv.org/abs/1605.05365)
- **Sharma, Lakshminarayanan & Ravindran (2017), "Learning to Repeat: Fine Grained Action Repetition for Deep RL" (FiGAR), ICLR.** Factored policy that outputs an action plus a separate repetition length, on top of A3C/TRPO/DDPG. Relevance: an early example of a learned decision duration. [S] — [arXiv 1702.06054](https://arxiv.org/abs/1702.06054)
- **Kalyanakrishnan, Aravindan, Bagdawat, Bhatt, Goka, Gupta, Krishna & Piratla (2021), "An Analysis of Frame-skipping in Reinforcement Learning", arXiv.** Theory and experiments on frame-skip. Skipping shortens the effective horizon and speeds learning, but costs optimality, so the skip length involves a trade-off. [S] — [arXiv 2102.03718](https://arxiv.org/abs/2102.03718)
- **Metelli, Mazzolini, Bisi, Sabbioni & Restelli (2020), "Control Frequency Adaptation via Action Persistence in Batch Reinforcement Learning", ICML.** Defines persistence-k MDPs, bounds the performance loss from persistence, proposes Persistent FQI, and gives a **heuristic for choosing the persistence level from batch data**. Relevance: **the closest prior work to a "data-driven, offline selector of decision granularity"**. It must be cited and contrasted in any novelty claim. [V] (found via search; metadata matches PMLR v119) — [arXiv 2002.06836](https://arxiv.org/abs/2002.06836) / [PMLR](https://proceedings.mlr.press/v119/metelli20a.html)
- **Biedenkapp, Rajan, Hutter & Lindauer (2021), "TempoRL: Learning When to Act", ICML.** A second "skip" Q-function decides how long to commit to the chosen action. This reduces the number of decisions and speeds up learning, and the paper shows that agents learn to act less often in uneventful states. Relevance: learned decision timing in a discrete MDP, directly transferable to "decide at this sensor reading or wait". [S] — [arXiv 2106.05262](https://arxiv.org/abs/2106.05262)
- **Dabney, Ostrovski & Barreto (2021), "Temporally-Extended ε-Greedy Exploration", ICLR.** Repeating random actions for heavy-tailed durations ("εz-greedy") fixes the poor exploration of per-step dithering. Relevance: explains one mechanism by which fine time steps hurt learnability. [S] — [arXiv 2006.01782](https://arxiv.org/abs/2006.01782)
- **Wang & Beltrame (2024), "Deployable Reinforcement Learning with Variable Control Rate" (SEAC: Soft Elastic Actor-Critic), arXiv.** SAC extension in which the policy outputs both the action and the duration of the time step. [V] — [arXiv 2401.09286](https://arxiv.org/abs/2401.09286)
- **Wang & Beltrame (2024), "MOSEAC: Streamlined Variable Time Step Reinforcement Learning", arXiv.** Tunes the agent's control-loop frequency automatically with a single hyperparameter. [V] — [arXiv 2406.01521](https://arxiv.org/abs/2406.01521)
- **Wang & Beltrame (2024), "Variable Time Step Reinforcement Learning for Robotic Applications", arXiv.** Argues the optimal control rate is task-dependent. Acting only when needed gives faster convergence and lower compute/energy than fixed rates. [V] — [arXiv 2407.00290](https://arxiv.org/abs/2407.00290)
- **TARC: Time-Adaptive Robotic Control (Oct 2025), arXiv.** Robot policies output an action plus how long to apply it. The control frequency rises state-dependently, e.g., a quadruped after a push. Authors not checked in this session. [V] (existence/abstract via search) — [arXiv 2510.23176](https://arxiv.org/abs/2510.23176)
- **"Select before Act: Spatially Decoupled Action Repetition for Continuous Control" (SDAR), ICLR 2025.** Makes a closed-loop act-or-repeat choice per action dimension. [V] (via search) — [ICLR 2025 poster page](https://www.iclr.cc/virtual/2025/poster/29767)
- **Karimi, Jin, Luo, Mahmood, Jagersand & Tosatto (2023), "Dynamic Decision Frequency with Continuous Options", IROS.** Continuous-time options that let the agent change its decision frequency at run time. [S] — [arXiv 2212.04407](https://arxiv.org/abs/2212.04407)
- **Farrahi & Mahmood (2023), "Reducing the Cost of Cycle-Time Tuning for Real-World Policy Optimization", IJCNN.** Shows that PPO/SAC hyperparameters tuned at one cycle time transfer poorly to others, and proposes cycle-time-aware rescaling rules (e.g., for γ, batch size). Relevance: a practical warning that a fair granularity comparison must rescale hyperparameters. [S] — [arXiv 2305.05760](https://arxiv.org/abs/2305.05760)
- **Mahmood, Korenkevych, Vasan, Ma & Bergstra (2018), "Setting up a Reinforcement Learning Task with a Real-World Robot", IROS.** Empirical: the action cycle time is one of the most performance-critical choices on real robots. [S] — [arXiv 1803.07067](https://arxiv.org/abs/1803.07067)

### Inferences
- In the IoT-PresPM setting, simply "deciding at every sensor reading" with a vanilla per-step Q-learner and unchanged γ is expected to *underperform* event-aligned decisions. This is a known failure mode (Tallec 2019; Park 2021), not an argument against fine granularity as such. A fair comparison must use dt-aware formulations (rescaled discount, advantage scaling, n-step adjusted to dt, or learned durations).
- Zhang et al. (2023) give theoretical backing for an interior optimum in granularity under finite data. That makes a "data-driven granularity selector" a well-posed object.

### Gaps
- No work found that studies dt-robustness specifically for *offline* learning from irregularly-sampled multivariate sensor streams with discrete start/stop actions (most results are online, continuous action, simulated robotics).
- Exact author lists for TARC (2510.23176) and SDAR were not checked.

---

## Q2. Learning *when* to act or observe: event-triggered RL, act/skip decisions, communication, and time-adaptive sensing

### Takeaway
A distinct line of work makes "when to decide or measure" an explicit decision with a cost. This includes event-triggered RL, lazy-MDPs, observation-cost MDPs, TaCoS and active observing. Two results recur: decision timing can be learned jointly with the action, and doing so cuts interactions or decisions substantially at the same or better return.

### Cited Findings
- **Jacq, Ferret, Pietquin & Geist (2022), "Lazy-MDPs: Towards Interpretable RL by Learning When to Act", AAMAS 2022.** Adds a "lazy" action that defers to a default policy and penalises taking control. Optimality is characterised in terms of the default policy and the penalty. On Atari with a random default policy, agents approach or beat DQN while acting in far fewer states. Relevance: in PresPM the default is "do nothing / keep spinning", and the agent should intervene only at a few sensor ticks. [V] — [arXiv 2203.08542](https://arxiv.org/abs/2203.08542)
- **Baumann, Zhu, Martius & Trimpe (2018), "Deep Reinforcement Learning for Event-Triggered Control", IEEE CDC.** Learns the control law and the communication/trigger policy jointly with DRL, saving communication versus periodic control. Relevance: a bridge between event-triggered control and RL. [S] — [arXiv 1809.05152](https://arxiv.org/abs/1809.05152)
- **Singh, Jain & Sukhbaatar (2019), "Learning when to Communicate at Scale in Multiagent Cooperative and Competitive Tasks" (IC3Net), ICLR.** A gating action decides at each step whether to communicate. Relevance: the "when-to-X" gating pattern. [S] — [arXiv 1812.09755](https://arxiv.org/abs/1812.09755)
- **Treven, Sukhija, As, Dörfler & Krause (2024), "When to Sense and Control? A Time-adaptive Approach for Continuous-Time RL" (TaCoS), NeurIPS 2024.** Reformulates continuous-time RL with costly interactions as an equivalent discrete-time MDP where the policy chooses an action and how long to hold it. Standard RL on TaCoS drastically reduces interactions at the same or better performance. Model-based OTaCoS has sublinear regret for smooth dynamics. Relevance: closest modern framework for "decisions at arbitrary times with a cost per decision". It is online, however. [V] — [arXiv 2406.01163](https://arxiv.org/abs/2406.01163)
- **Treven, Hübotter, Sukhija, Dörfler & Krause (2023), "Efficient Exploration in Continuous-time Model-based Reinforcement Learning", NeurIPS.** Optimistic model-based continuous-time RL with regret bounds. It also studies *measurement selection strategies* (when to sample the state) and shows that adaptive measurement times matter for regret. [S] — [arXiv 2310.19698](https://arxiv.org/abs/2310.19698)
- **Holt, Hüyük, Qian, Sun & van der Schaar (2023), "Active Observing in Continuous-time Control", NeurIPS.** Formalises continuous-time control with costly observations. Shows that regular (fixed-interval) observing is suboptimal and that irregular, adaptively chosen observation times can be better. Proposes an MPC-based method (Active Observing Control). Relevance: theoretical support for "event/state-triggered beats clock-triggered", in a continuous-time model-based setting. [S] — [arXiv 2305.18441](https://arxiv.org/abs/2305.18441)
- **Yildiz, Heinonen & Lähdesmäki (2021), "Continuous-Time Model-Based Reinforcement Learning", ICML.** Neural-ODE (Bayesian) dynamics models enabling RL with irregular, arbitrary-time observations and control. Relevance: a way to learn from irregularly-sampled IoT data without binning. [S] — [arXiv 2102.04764](https://arxiv.org/abs/2102.04764)
- **Nam, Fleming & Brunskill (2021), "Reinforcement Learning with State Observation Costs in Action-Contingent Noiselessly Observable MDPs", NeurIPS.** Observation as a costly action. [S] — [Semantic Scholar search](https://www.semanticscholar.org/search?q=Reinforcement%20Learning%20with%20State%20Observation%20Costs%20in%20Action-Contingent%20Noiselessly%20Observable%20Markov%20Decision%20Processes)
- **Krale, Simão & Jansen (2023), "Act-Then-Measure: RL for Partially Observable Environments with Active Measuring", ICAPS.** Same theme, a heuristic that separates control from measurement decisions. [S] — [Semantic Scholar search](https://www.semanticscholar.org/search?q=Act-Then-Measure%20Reinforcement%20Learning%20for%20Partially%20Observable%20Environments%20with%20Active%20Measuring)

### Inferences
- The thesis's start/stop problem can be cast as a lazy-MDP or TaCoS-style problem: at each sensor tick, choose between "no-op" (or "hold") and a costly decision. This turns "decide at arbitrary times" into a learnable gating policy rather than an exhaustive per-tick action.
- Almost all of this line is *online* (simulator-based) and continuous-control oriented. Offline, logged-data versions for business-process / IoT settings appear to be missing.

### Gaps
- No offline (logged-data-only) version of TaCoS / active observing found.

---

## Q3. Semi-MDPs, options and temporal abstraction; discount and horizon under finer steps

### Takeaway
Semi-MDPs and options are the standard formalism for decisions at variable, state-dependent times. With finer steps, discount and effective horizon must be rescaled (γ = e^{−dt/τ}). Otherwise both the problem definition and the bias/variance of learning change silently: the horizon in steps grows as 1/dt, and bootstrapped value propagation slows down accordingly.

### Cited Findings
- **Sutton, Precup & Singh (1999), "Between MDPs and semi-MDPs: A Framework for Temporal Abstraction in RL", *Artificial Intelligence* 112.** Defines options (initiation set, intra-option policy, termination) and shows that an MDP plus options forms an SMDP, with discounting γ^k over variable durations. Relevance: event-aligned decisions = an SMDP over the sensor-level MDP. This is the formal link between "event granularity" and "sensor granularity". [S] — [DOI 10.1016/S0004-3702(99)00052-1](https://doi.org/10.1016/S0004-3702(99)00052-1)
- **Bradtke & Duff (1994), "Reinforcement Learning Methods for Continuous-Time Markov Decision Problems", NIPS 7.** SMDP Q-learning / TD with exponential discounting over random sojourn times. [S] — [Semantic Scholar search](https://www.semanticscholar.org/search?q=Reinforcement%20Learning%20Methods%20for%20Continuous-Time%20Markov%20Decision%20Problems)
- **Bacon, Harb & Precup (2017), "The Option-Critic Architecture", AAAI.** Learns option policies and termination functions end-to-end. Learned terminations amount to learned decision times. [S] — [arXiv 1609.05140](https://arxiv.org/abs/1609.05140)
- **Burns, Yu, Finn & Hausman, "Offline Reinforcement Learning at Multiple Frequencies", CoRL (PMLR v205; listed as CoRL 2022 by mlanthology, PMLR volume published 2023).** In offline RL, Q-values propagate at different rates under different discretizations, so naively mixing datasets at different control frequencies destabilises learning. Scaling N in N-step returns to the discretization ("adaptive N-step") fixes this and beats naive mixing by about 50% on average on three simulated robot tasks. Relevance: directly relevant to logs where event-level and sensor-level transitions co-exist. [V] — [arXiv 2207.13082](https://arxiv.org/abs/2207.13082) / [PMLR](https://proceedings.mlr.press/v205/burns23a.html)
- **Pardo, Tavakoli, Levdik & Kormushev (2018), "Time Limits in Reinforcement Learning", ICML.** Correct treatment of time-limit terminations vs true terminals (include remaining time in the state; bootstrap at timeouts). Relevance: process cases and spinning steps have finite durations. [S] — [arXiv 1712.00378](https://arxiv.org/abs/1712.00378)
- **Jiang, Kulesza, Singh & Lewis (2015), "The Dependence of Effective Planning Horizon on Model Accuracy", AAMAS.** A smaller-than-true discount acts as a complexity regulariser under limited data. Relevance: granularity and discount interact as joint regularisers. [S] — [Semantic Scholar search](https://www.semanticscholar.org/search?q=The%20Dependence%20of%20Effective%20Planning%20Horizon%20on%20Model%20Accuracy)
- **Amit, Meir & Ciosek (2020), "Discount Factor as a Regularizer in Reinforcement Learning", ICML.** Formal equivalence between lower discount in TD and regularisation. [S] — [arXiv 2007.02040](https://arxiv.org/abs/2007.02040)

### Inferences
- Comparing event-aligned and sensor-aligned policies is, formally, comparing an SMDP policy (options = "wait until next event") with a primitive-action policy on the finer MDP. The sensor-level policy class contains the event-level one. Any gain or loss from finer granularity is therefore a *learnability/estimation* effect (variance, horizon, exploration) rather than an *expressiveness* effect. This framing is useful for the thesis.
- With finer steps, γ must be set as e^{−dt/τ} to keep the same objective. Comparing granularities with a fixed γ changes the problem itself.

### Gaps
- I did not find a paper titled "Reining in the curse of horizon" or "Coarse-to-fine" in the temporal (rather than action-space) sense. The closest temporal-resolution offline work is Burns et al. and Metelli et al.

---

## Q4. Off-policy evaluation (OPE) and the curse of horizon: how does the number of decision points affect estimator variance?

### Takeaway
Trajectory importance sampling has variance that can grow exponentially in the number of decision points. Finer granularity therefore directly worsens offline evaluation unless one uses temporal abstraction (options), marginalised/stationary-distribution IS, or model-/Q-based estimators. New 2024–2026 work shows that discretizing irregular decision times (binning) can bias both learning and OPE badly, and proposes timing-aware OPE.

### Cited Findings
- **Liu, Li, Tang & Zhou (2018), "Breaking the Curse of Horizon: Infinite-Horizon Off-Policy Estimation", NeurIPS.** Names the "curse of horizon": IS variance explodes with trajectory length. Proposes importance weighting on the stationary state-visitation distribution ratio, avoiding products of per-step ratios. [S] — [arXiv 1810.12429](https://arxiv.org/abs/1810.12429)
- **Guo, Thomas & Brunskill (2017), "Using Options and Covariance Testing for Long Horizon Off-Policy Policy Evaluation", NeurIPS.** IS variance can grow exponentially with the number of sequential decisions. Evaluating option-based policies instead of primitive-action policies can reduce variance exponentially, sometimes making it horizon-independent, and needs far less data. Reviewers found the experiments somewhat artificial. Relevance: **direct evidence that coarser decision granularity (fewer decision points) makes OPE easier**. This is half of the granularity-vs-learnability trade-off. [V] — [arXiv 1703.03453](https://arxiv.org/abs/1703.03453)
- **Jiang & Li (2016), "Doubly Robust Off-policy Value Evaluation for Reinforcement Learning", ICML.** Doubly-robust sequential OPE that lowers IS variance using a learned Q model. [V] (appeared in search) — [arXiv 1511.03722](https://arxiv.org/abs/1511.03722)
- **Xie, Ma & Wang (2019), "Towards Optimal Off-Policy Evaluation for Reinforcement Learning with Marginalized Importance Sampling", NeurIPS.** Marginalised IS with error polynomial rather than exponential in horizon (finite-horizon tabular). [S] — [arXiv 1906.03393](https://arxiv.org/abs/1906.03393)
- **Kallus & Uehara (2020), "Double Reinforcement Learning for Efficient Off-Policy Evaluation in MDPs", JMLR.** Efficiency bounds for OPE. In MDPs, efficient estimators avoid the curse of horizon present in NMDP/trajectory IS. [S] — [arXiv 1908.08526](https://arxiv.org/abs/1908.08526)
- **Uehara, Shi & Kallus (2022), "A Review of Off-Policy Evaluation in Reinforcement Learning", arXiv.** Survey of IS, DR, marginalised and model-based OPE and their horizon dependence. [S] — [arXiv 2212.06355](https://arxiv.org/abs/2212.06355)
- **Chen et al. (2024), "Off-Policy Evaluation with Irregularly-Spaced, Outcome-Dependent Observation Times", arXiv.** Models a state-action process jointly with an observation process that decides *when* decisions happen, linking MDPs and renewal processes. Derives value functions (cumulative and integrated reward) and inference under revised Markov/time-homogeneity assumptions on gap times. Relevance: OPE when decision times are themselves data-dependent, as in IoT logs where a human acts at irregular sensor moments. [V] — [arXiv 2409.09236](https://arxiv.org/abs/2409.09236)
- **Wald, Goldstein, Efroni, van Amsterdam & Ranganath (2025), "Time After Time: Deep-Q Effect Estimation for Interventions on When and What to do" (EDQ), arXiv.** Treats decision timing as a point process. "Earliest Disagreement Q-Evaluation" is a model-free deep-Q estimator of the effect of policies that choose both *when* and *what*. It avoids time discretization, works with transformers, and is validated on survival and tumour-growth tasks. Venue: the arXiv page lists none, while a search snippet claimed ICLR 2025 (**conflict, unresolved**). Relevance: **the closest method for offline evaluation of start/stop policies at arbitrary times**. [V] — [arXiv 2503.15890](https://arxiv.org/abs/2503.15890)
- **Frost, Vaidya & Harris (2026), "The impact of temporal resampling on the safety of clinical reinforcement learning: A simulated trial" (earlier title "The hidden risks of temporal resampling in clinical RL"), arXiv; stated as in press at *PLOS Digital Health* (v4, 15 Oct 2026).** In MIMIC-IV, binning reversed the apparent causal order for over 70% of paired glucose measurements and insulin adjustments. In an FDA-approved T1D simulator, resampling at 10 min, 2 h and 4 h cut deployed offline-RL performance by up to 60% relative to unbinned data, with 4 h binning worse than the behaviour policy for all agents. Retrospective OPE on resampled data over-predicted deployed returns by 1.5–3x. Relevance: **strong recent evidence that the choice of decision grid affects both learned-policy quality and OPE validity, and that coarse binning misleads OPE**. Directly supports the thesis motivation. [V] — [arXiv 2602.06603](https://arxiv.org/abs/2602.06603)

### Inferences
- Granularity creates a two-sided trade-off for OPE. Finer grids mean more decision points, so IS-type variance grows (Liu 2018; Guo 2017). Coarser or binned grids introduce bias: causal-order violations and model misspecification (Frost 2026; Zhang 2023's approximation error). For a stopping policy, the IS weight is a product over all "continue" steps before stopping. Halving dt roughly doubles the number of factors, unless the behaviour and target policies agree on most ticks (e.g., both "continue" with high probability).
- OPE-based model selection across granularities (the "selector") therefore needs estimators whose variance does not scale with the number of ticks: DR/FQE, marginalised IS, or timing-aware estimators like EDQ. Otherwise the selector will be systematically biased toward coarse granularities.

### Gaps
- No paper found that uses OPE specifically to *select* the decision granularity from logged data and analyses the selection bias this induces. This is a candidate novelty point.

---

## Q5. Optimal stopping, learning to stop from data, when-to-treat, and early classification of time series

### Takeaway
Stopping a spinning step is an optimal stopping problem. Deep optimal stopping and regression-based (Longstaff–Schwartz) methods learn stopping rules from simulated paths. "When-to-treat" policy learning and timing-aware OPE extend this to observational data, and early classification of time series (ECTS) is an earliness-accuracy special case of optimal stopping. Purely offline, observational stopping/starting with continuous sensor covariates remains thinly covered.

### Cited Findings
- **Longstaff & Schwartz (2001), "Valuing American Options by Simulation: A Simple Least-Squares Approach", *Review of Financial Studies* 14(1).** Regression of continuation values on basis functions along simulated paths. This is the template for "learning to stop from trajectories". [S] — [DOI 10.1093/rfs/14.1.113](https://doi.org/10.1093/rfs/14.1.113)
- **Tsitsiklis & Van Roy (1999), "Optimal Stopping of Markov Processes: Hilbert Space Theory, Approximation Algorithms, and an Application to Pricing High-Dimensional Financial Derivatives", *IEEE TAC* 44(10).** Q-learning/TD for optimal stopping with linear function approximation, with convergence guarantees. [S] — [DOI 10.1109/9.793723](https://doi.org/10.1109/9.793723)
- **Becker, Cheridito & Jentzen (2019), "Deep Optimal Stopping", *JMLR* 20.** Decomposes the stopping time into a sequence of 0/1 stopping decisions, each a neural network trained backward in time. Gives lower/upper bounds and confidence intervals, and scales to high dimension (e.g., Bermudan max-call). Relevance: a natural baseline for a "stop spinning" policy defined on a fixed sensor grid. Note that it presupposes a fixed set of exercise (decision) dates. [S] — [arXiv 1804.05394](https://arxiv.org/abs/1804.05394)
- **Herrera, Krach, Ruyssen & Teichmann (2021/2024), "Optimal Stopping via Randomized Neural Networks", arXiv (later in *Frontiers of Mathematical Finance*).** Randomised hidden layers so that only the last layer is fit by least squares, giving fast, convergent LSM- and RL-style stopping algorithms. [S] — [arXiv 2104.13669](https://arxiv.org/abs/2104.13669)
- **Nie, Brunskill & Wager (2021), "Learning When-to-Treat Policies", *JASA* 116.** Learns a dynamic policy that decides *when* to start a treatment (a starting/stopping-type problem) from observational data, using an advantage-doubly-robust estimator under sequential ignorability, with regret guarantees. Relevance: **the causal-inference counterpart of the thesis's "when to start" decision**, offline and from observational data. [S] — [arXiv 1905.09751](https://arxiv.org/abs/1905.09751)
- **"Policy Learning for Optimal Dynamic Treatment Regimes with Observational Data" (2024), arXiv.** Treats optimal stopping/starting as a constrained DTR policy class learned under sequential ignorability. Authors not checked; described via search snippet. [V] (existence) — [arXiv 2404.00221](https://arxiv.org/abs/2404.00221)
- **Kuchko (2025), "DO-IQS: Dynamics-Aware Offline Inverse Q-Learning for Optimal Stopping with Unknown Gain Functions", arXiv.** Offline *inverse* optimal stopping: recovers the stopping region from stopped expert trajectories by approximating continuation and stopping gains in a "Stopped MDP". Addresses data sparsity near the stopping boundary. Relevance: if the logs contain operator stop times but no explicit reward, this is the relevant offline formulation. [V] — [arXiv 2503.03515](https://arxiv.org/abs/2503.03515)
- **arXiv 1702.06238 (2017).** Learning near-optimal stopping policies with unknown dynamics via off-policy evaluation. The authors note OPE is high-variance in this setting. Title and authors not verified (search snippet only). [V-partial] — [arXiv 1702.06238](https://arxiv.org/abs/1702.06238)
- **Dachraoui, Bondu & Cornuéjols (2015), "Early Classification of Time Series as a Non Myopic Sequential Decision Making Problem", ECML PKDD.** Casts ECTS as cost optimisation: misclassification cost plus a time-dependent delay cost. It estimates the expected future cost of waiting and triggers when the current cost is minimal (non-myopic). Relevance: directly analogous to the cost of stopping now versus at the next sensor tick. [S] — [Semantic Scholar search](https://www.semanticscholar.org/search?q=Early%20classification%20of%20time%20series%20as%20a%20non%20myopic%20sequential%20decision%20making%20problem)
- **Hartvigsen, Sen, Kong & Rundensteiner (2019), "Adaptive-Halting Policy Network for Early Classification", KDD.** An RL halting policy on top of an RNN classifier that decides at each time step whether to stop and classify, with an earliness-accuracy trade-off. [S] — [DOI 10.1145/3292500.3330974](https://doi.org/10.1145/3292500.3330974)
- **Renault, Bondu & Cornuéjols (2024), "Early Classification of Time Series: A Survey and Benchmark", arXiv.** Taxonomy plus a benchmark of ECTS methods. Argues the field lacks a shared evaluation protocol, and frames ECTS as a special case of optimal stopping. [V] — [arXiv 2406.18332](https://arxiv.org/abs/2406.18332)
- **Gupta, Gupta, Biswas & Dutta (2020), "Approaches and Applications of Early Classification of Time Series: A Review", arXiv / IEEE TAI.** Review of ECTS approaches (prefix-based, shapelet, model-based, RL-based). [V] — [arXiv 2005.02595](https://arxiv.org/abs/2005.02595)
- **Akasiadis et al. (2022), empirical comparison of ECTS methods, arXiv.** TEASER, MLSTM and ECEC gave the best accuracy/earliness, and ECONOMY-K was fastest to train. [V] — [arXiv 2203.01628](https://arxiv.org/abs/2203.01628)
- **Xing, Pei & Keogh (2012), "Early Classification on Time Series" (ECTS), *Knowledge and Information Systems*.** Introduced the ECTS minimum-prediction-length approach. [S] — [Semantic Scholar search](https://www.semanticscholar.org/search?q=Early%20classification%20on%20time%20series%20Xing%20Pei%20Keogh)

### Inferences
- The cotton-candy stop decision maps onto ECTS/optimal stopping, with the triggering (decision) grid as a free parameter. Deep optimal stopping and ECTS methods both assume a fixed observation grid. The impact of that grid's resolution on earliness-cost estimation and generalisation appears unexplored in this line of work.
- "When to start" plus "when to stop" make a two-stopping-time (switching) problem. Nie et al. (start) and stopping methods (stop) each cover one side. A joint offline treatment with sensor covariates seems rare.

### Gaps
- No paper found that studies how the resolution of the decision grid affects the learnability of a stopping rule from *offline* observational data, beyond the general results in Q1/Q4.

---

## Q6. Event-triggered vs time-triggered control

### Takeaway
Control theory has long shown that event-triggered (Lebesgue) sampling can match or beat periodic (Riemann) sampling at the same or a lower average sampling rate. This is a model-based precedent for "decide when the state warrants it" over "decide every tick".

### Cited Findings
- **Åström & Bernhardsson (2002), "Comparison of Riemann and Lebesgue Sampling for First Order Stochastic Systems", IEEE CDC.** For a first-order stochastic system, event-based (Lebesgue) sampling gives lower output variance than periodic sampling at the same average sampling rate. [S] — [DOI 10.1109/CDC.2002.1184824](https://doi.org/10.1109/CDC.2002.1184824)
- **Heemels, Johansson & Tabuada (2012), "An Introduction to Event-triggered and Self-triggered Control", IEEE CDC.** Tutorial on event-triggered control (trigger when a state-error condition is violated) and self-triggered control (the controller computes its next update time), covering stability and Zeno-behaviour issues. [S] — [DOI 10.1109/CDC.2012.6425820](https://doi.org/10.1109/CDC.2012.6425820)
- **Baumann et al. (2018)**, see Q2: learned event-triggering with DRL. [S] — [arXiv 1809.05152](https://arxiv.org/abs/1809.05152)

### Inferences
- In PresPM terms, *process events* resemble an exogenous event-triggering rule (decisions happen when the process logs something), while *sensor ticks* are time-triggered sampling. The thesis can frame its question as which triggering rule (exogenous events, periodic, or learned self-triggering) gives the best decision quality per decision. Control theory says the answer depends on the dynamics, not on which grid is finer.

### Gaps
- Event-triggered control results are mostly model-based with known dynamics. Data-driven/offline analogues are rare (beyond Baumann 2018, which is online).

---

## Q7. Predictive maintenance / condition-based decisions from sensor streams; PresPM timing work

### Takeaway
Maintenance-timing RL is mostly online/simulated. Offline RL from historical sensor and event logs exists but is sparse. In process mining, "when to intervene" has a small PresPM literature (alarm-based monitoring, Metzger/Fahrenkrog-Petersen, Shoush & Dumas, KU Leuven's Weytjens et al.). In all of it, decision points are aligned with events/prefixes, never with sensor readings.

### Cited Findings
- **Khorasgani, Wang, Gupta & Farahat (2021), "An Offline Deep Reinforcement Learning for Maintenance Decision-Making", arXiv (Hitachi).** Learns maintenance policies (continue vs intervene) from historical logs that combine time-series sensor data and discrete event logs, without a simulator. Relevance: the closest predictive-maintenance analogue to IoT-enriched event logs plus offline RL. [V] — [arXiv 2109.15050](https://arxiv.org/abs/2109.15050)
- **Ong, Niyato & Yuen (2020), "Predictive Maintenance for Edge-Based Sensor Networks: A Deep Reinforcement Learning Approach", arXiv / IEEE WF-IoT.** DRL with repair/replace/hold actions on sensor windows (online). [V] — [arXiv 2007.03313](https://arxiv.org/abs/2007.03313)
- **Weytjens, Verbeke & De Weerdt (2023), "Timing Process Interventions with Causal Inference and Reinforcement Learning", arXiv / BPM workshops (KU Leuven).** Compares CI and online RL for *timing* a process intervention on synthetic data. RL policies outperform CI and are more robust, while CI remains useful when online learning is impossible. Relevance: same research group context, and the closest PresPM work on timing. Decisions there are made at event steps. [V] — [arXiv 2306.04299](https://arxiv.org/abs/2306.04299)
- **Shoush & Dumas (2022), "When to Intervene? Prescriptive Process Monitoring Under Uncertainty and Resource Constraints", arXiv / BPM Forum.** Decides if and when to trigger an intervention per case, trading off acting now against later, under resource constraints. Uses predictive and causal models, not RL. [V] — [arXiv 2206.07745](https://arxiv.org/abs/2206.07745)
- **Teinemaa, Tax, de Leoni, Dumas & Maggi (2018), "Alarm-Based Prescriptive Process Monitoring", BPM Forum.** Raises an alarm (intervention) when a predicted probability of an undesired outcome exceeds a cost-optimised threshold, evaluated at each prefix length. This is an earliness-cost trade-off. [S] — [arXiv 1803.08706](https://arxiv.org/abs/1803.08706)
- **Fahrenkrog-Petersen, Tax, Teinemaa, Dumas, de Leoni, Maggi & Weidlich (2022), "Fire Now, Fire Later: Alarm-Based Systems for Prescriptive Process Monitoring", *Knowledge and Information Systems*.** Extends alarm-based PresPM with intervention effectiveness that decays over time and with cost models. [S] — [arXiv 1905.09568](https://arxiv.org/abs/1905.09568)
- **Metzger, Kley & Palm (2020), "Triggering Proactive Business Process Adaptations via Online Reinforcement Learning", BPM.** Uses predictions and their reliability estimates with online RL to learn when to trigger proactive adaptations. Described secondhand via search. [S] — [Semantic Scholar search](https://www.semanticscholar.org/search?q=Triggering%20Proactive%20Business%20Process%20Adaptations%20via%20Online%20Reinforcement%20Learning)
- **Bozorgi, Teinemaa, Dumas, La Rosa & Polyvyanyy (2023), "Prescriptive Process Monitoring Based on Causal Effect Estimation", *Information Systems*.** Uses uplift/CATE models to decide which cases to treat, with conformal-style triggering rules. [S] — [Semantic Scholar search](https://www.semanticscholar.org/search?q=Prescriptive%20process%20monitoring%20based%20on%20causal%20effect%20estimation)

### Inferences
- Every PresPM timing paper found defines candidate decision points as *prefixes/events*. None treats intra-event sensor readings as decision points or compares the two. This supports the thesis's novelty claim about IoT-enriched decision granularity in PresPM.

### Gaps
- Offline RL applied to maintenance timing with conservative methods (CQL/IQL) on real industrial sensor logs appears limited. Only the Hitachi paper was found in this session.

---

## Q8. Choosing or learning the decision granularity from data (novelty-critical)

### Takeaway
Prior work on adapting granularity falls into four groups:
- **Online learned durations:** FiGAR, TempoRL, SEAC/MOSEAC, TaCoS, TARC, SAR, option-critic.
- **Adaptive *state/action-space* discretization:** Sinclair et al.; this is spatial, not temporal.
- **Theory of an optimal time step under a data budget:** Zhang et al. 2023.
- **Offline persistence selection:** Metelli et al. 2020, the closest prior.

No work found builds an offline, OPE-driven selector that compares event-aligned and sensor-aligned (or multi-resolution) decision grids on logged process or IoT data.

### Cited Findings
- **Sinclair, Banerjee & Yu (2019/2020), "Adaptive Discretization for Episodic Reinforcement Learning in Metric Spaces", SIGMETRICS / POMACS.** Adaptive Q-learning that refines the *state-action* partition where data and value warrant it, with regret bounds depending on the zooming dimension. Relevance: the methodological template for a data-adaptive partition. It adapts the space, not decision times. [S] — [arXiv 1910.08151](https://arxiv.org/abs/1910.08151)
- **Metelli et al. (2020)** (see Q1): persistence/control-frequency selection from batch data, with Persistent FQI and a heuristic selection criterion. **The closest prior work. A thesis novelty claim must distinguish itself from it**, e.g., by event-aligned vs sensor-aligned grids that are non-uniform and exogenous, an OPE-based selector with horizon-robust estimators, process/IoT data, and start/stop structure. [V] — [arXiv 2002.06836](https://arxiv.org/abs/2002.06836)
- **Zhang et al. (2023)** (see Q1): an optimal temporal resolution exists for a given data budget (LQR theory plus benchmarks), and the authors suggest tuning it. [V] — [arXiv 2212.08949](https://arxiv.org/abs/2212.08949)
- **Burns et al. (CoRL)** (see Q3): handles mixed frequencies offline. It does not select one. [V] — [arXiv 2207.13082](https://arxiv.org/abs/2207.13082)
- **Treven et al. (2024) TaCoS** (see Q2): learns hold durations online with an interaction cost. [V] — [arXiv 2406.01163](https://arxiv.org/abs/2406.01163)
- **Wang & Beltrame (2024) SEAC/MOSEAC/VTS-RL** and **TARC (2025)** (see Q1): learn variable time steps online. [V] — [arXiv 2401.09286](https://arxiv.org/abs/2401.09286), [arXiv 2406.01521](https://arxiv.org/abs/2406.01521), [arXiv 2510.23176](https://arxiv.org/abs/2510.23176)
- **Frost et al. (2026)** (see Q4): show empirically that the grid choice matters and that OPE on resampled data misleads. They recommend natural timing but do not propose a selector. [V] — [arXiv 2602.06603](https://arxiv.org/abs/2602.06603)
- **Wald et al. (2025) EDQ** and **Chen et al. (2024)** (see Q4): avoid choosing a grid by modelling decision times as a point/renewal process. This is the "no-discretization" alternative to a selector. [V] — [arXiv 2503.15890](https://arxiv.org/abs/2503.15890), [arXiv 2409.09236](https://arxiv.org/abs/2409.09236)

### Inferences

**Synthesis: how decision frequency affects learnability, sample efficiency, bias/variance and offline evaluation**
1. *Expressiveness vs estimation.* A finer decision grid weakly enlarges the policy class (the SMDP view, Sutton et al. 1999), so any loss from fine granularity is an estimation/optimisation effect.
2. *Value learning.* As dt→0, advantages shrink as O(dt), Q collapses onto V, and per-step Q-learning loses its signal (Baird 1994; Tallec 2019). The fix is dt-scaled advantages or continuous-time q-functions (Jia & Zhou 2023).
3. *Horizon/propagation.* With γ = e^{−dt/τ}, the effective horizon in steps is about τ/dt. Bootstrapped values propagate 1/dt times slower per update, which motivates n-step returns scaled to dt (Burns et al.). Frame-skip shortens the horizon at the cost of optimality (Kalyanakrishnan 2021).
4. *Exploration.* Per-step dithering at fine dt explores poorly. Temporally extended exploration is needed (Dabney 2021; Tallec 2019).
5. *Policy-gradient variance.* Variance diverges as dt→0 without repetition or reparametrisation (Park 2021; Munos 2006).
6. *Bias-variance in time.* Coarse grids add approximation and discretization bias. Fine grids add statistical variance under a fixed data budget. An interior optimum exists (Zhang 2023, proven for LQR/MC evaluation).
7. *OPE.* Trajectory-IS variance grows exponentially with the number of decision points. Options or coarser decisions reduce it (Guo 2017), and marginalised, DR or Q-based estimators mitigate it (Liu 2018; Xie 2019; Kallus & Uehara 2020). Binning irregular decisions biases OPE upward, by 1.5–3x in a clinical simulation (Frost 2026).
8. *Learned timing.* Making "act now vs hold" a decision (TempoRL, Lazy-MDP, TaCoS, SAR) consistently reduces decision counts while keeping or improving return, mostly shown online.

**Novelty assessment for the thesis.** The following combination appears unoccupied in the literature found:
- PresPM/event logs enriched with IoT sensor streams;
- an explicit comparison of event-aligned vs sensor-aligned (or multi-resolution) decision points for start/stop timing;
- learning and evaluation fully offline;
- a data-driven selector of granularity based on horizon-robust OPE.

The thesis must cite and differentiate from Metelli et al. 2020 (batch persistence selection), Zhang et al. 2023 (optimal resolution theory), Burns et al. (offline multi-frequency), and Frost et al. 2026 (empirical harm of resampling in offline RL). A hypothesis consistent with the literature: the selector's estimated value will show an interior optimum in granularity, and the optimum shifts finer as the dataset grows.

### Gaps
- No paper found that does offline, OPE-based selection among non-uniform (event-driven) and uniform (sensor-driven) decision grids, or that analyses the selection bias of OPE across granularities (IS estimators favour coarse grids through lower variance, not higher value).
- No search was done specifically for 2026 conference papers (ICML/NeurIPS 2026) on decision-frequency selection. Coverage after mid-2025 rests on general arXiv searches, so a final 2026-specific check is advisable.
- I could not identify specific papers matching the prompt's working titles "Act only when it pays", "Reining in the curse of horizon", "Coarse-to-fine" (temporal) or "Action-repeat in offline RL". They may not exist under those names. Metelli 2020 and Burns et al. are the closest real matches for the latter two.
