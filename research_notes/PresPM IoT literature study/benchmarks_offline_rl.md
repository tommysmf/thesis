# Semi-synthetic benchmarks and offline policy learning for sequential decisions (PresPM + IoT)

Legend for every entry: **[V]** = verified in this research session (the paper/page showed up in a live search or fetch on 2026-10-31, and the metadata was checked there). **[S]** = secondhand: taken from the researcher's prior knowledge, and the link was written from memory without being opened in this session. Most [S] links are canonical arXiv/DOI identifiers that I'm confident about, but check each one before citing. Coverage runs to Oct 2026, but the search turned up almost nothing dated after mid-2026.

---

## 1. Semi-synthetic causal benchmarks (static treatment effect) and their known pitfalls

### Takeaway
The field has moved from hand-made response surfaces on real covariates (IHDP, ACIC) to generators *fitted to the real data* whose causal knobs can be set (RealCause, Credence, Frugal Flows / Frengression, WGAN-based Monte Carlo). The main lesson from the critical literature (Curth et al. 2021) is that the DGP's design choices can systematically favour some estimator families. Benchmark designers should therefore report and vary those choices: effect heterogeneity, overlap, confounding strength, and outcome-model class.

### Cited Findings (annotated list)
- **Hill (2011), "Bayesian Nonparametric Modeling for Causal Inference", J. Comput. Graph. Stat.** Introduces the IHDP semi-synthetic benchmark: real covariates from an RCT, a treated subgroup removed to create imbalance, and simulated response surfaces (setting "B" = nonlinear). It is the canonical "real X, synthetic Y" template. Relevance: same template as "real sensor trace, simulated outcome". [S] — [DOI 10.1198/jcgs.2010.08162](https://doi.org/10.1198/jcgs.2010.08162)
- **Dorie, Hill, Shalit, Scott, Cervone (2019), "Automated versus do-it-yourself methods for causal inference: Lessons learned from a data analysis competition", Statistical Science.** ACIC 2016 used 77 DGP settings that vary nonlinearity, overlap, effect heterogeneity and alignment on real covariates. Flexible nonparametric methods (BART-based) did well, and performance depended strongly on the DGP knobs. Relevance: the template for a *factorial* benchmark design. [S] — [arXiv 1707.02641](https://arxiv.org/abs/1707.02641)
- **Shalit, Johansson, Sontag (2017), "Estimating individual treatment effect: generalization bounds and algorithms" (TARNet/CFR), ICML.** Popularised IHDP-100 replications and PEHE as the metric. Relevance: TARNet is a base learner inside ProCause. [S] — [arXiv 1606.03976](https://arxiv.org/abs/1606.03976)
- **Curth, Svensson, Weatherall, van der Schaar (2021), "Really Doing Great at Estimating CATE? A Critical Look at ML Benchmarking Practices in Treatment Effect Estimation", NeurIPS Datasets & Benchmarks.** The authors argue that semi-synthetic datasets, unlike real benchmarks elsewhere in ML, *can systematically favour some algorithms over others*, focusing on IHDP. They also argue that common metrics cover only a small subset of CATE use cases. The earlier arXiv version covered IHDP and ACIC2016. — [V] [NeurIPS D&B PDF](https://datasets-benchmarks-proceedings.neurips.cc/paper/2021/file/2a79ea27c279e471f4d180b08d62b00a-Paper-round2.pdf); [arXiv 2107.13346](https://arxiv.org/abs/2107.13346)
- **Neal, Huang, Raghupathi (2020), "RealCause: Realistic Causal Inference Benchmarking", arXiv.** Fits generative models for p(T|X) and p(Y|T,X) to real data, checks that samples are statistically indistinguishable from the real data, and then exposes ground-truth potential outcomes. Overlap and confounding can be adjusted. Code: github.com/bradyneal/realcause. Relevance: the closest static analogue of the thesis's "fit models to the real IoT log, then simulate counterfactuals" step, and the basis of ProCause. [S] — [arXiv 2011.15007](https://arxiv.org/abs/2011.15007)
- **Parikh, Varjao, Xu, Tchetgen Tchetgen (2022), "Validating Causal Inference Methods" (Credence), ICML 2022.** Trains a deep generative model (conditional VAE in the slides) on the observed sample, then imposes user-designed treatment-effect and selection-bias functions. Evaluated on Lalonde and Project STAR. The authors report that it reproduces the oracle's ranking of estimators, except for variances. Stated limitations: generative models are sensitive to hyperparameters, and "evaluations are only as good as the user's assumptions". — [V] [arXiv 2202.04208](https://arxiv.org/abs/2202.04208); [ICML poster](https://icml.cc/virtual/2022/poster/16511)
- **Schuler, Jung, Tibshirani, Hastie, Shah (2017), "Synth-validation: Selecting the best causal inference method for a given dataset", arXiv.** Generates synthetic datasets that look like the observed one with a range of plausible effect sizes, then picks the estimator that does best across them. Relevance: method selection on a dataset-specific semi-synthetic benchmark. [S] — [arXiv 1711.00083](https://arxiv.org/abs/1711.00083)
- **Athey, Imbens, Metzger, Munro (2021/2024), "Using Wasserstein Generative Adversarial Networks for the design of Monte Carlo simulations", J. Econometrics.** Fits WGANs to Lalonde-type data so that Monte Carlo studies of estimators mimic the real data. Estimator rankings change with the DGP. [S] — [arXiv 1909.02210](https://arxiv.org/abs/1909.02210)
- **Evans & Didelez (2024), "Parameterizing and simulating from causal models" (frugal parameterization), JRSSB.** Splits the model into the margin of interest (the causal effect), the past, and a dependence measure (copula), so the causal estimand can be specified exactly while the rest is fitted to the data. [S] — [arXiv 2109.03694](https://arxiv.org/abs/2109.03694)
- **de Vassimon Manela, Battaglia, Evans (2024), "Marginal Causal Flows for Validation and Inference" (Frugal Flows), NeurIPS 2024.** Normalising-flow model that exactly parameterises the ATE and lets the user set the degree of *unobserved* confounding, so benchmarks can stress-test ignorability. — [V] [arXiv 2411.01295](https://arxiv.org/abs/2411.01295); [NeurIPS PDF](https://proceedings.neurips.cc/paper_files/paper/2024/file/1343e23bc2d34c054040e73ad86582cf-Paper-Conference.pdf)
- **Yang, Evans, Shen (2025), "Frugal, Flexible, Faithful: Causal Data Simulation via Frengression", arXiv.** Frugal parameterization with engression-based generators. Needs minimal tuning and extrapolates beyond the observed support. — [V] [arXiv 2508.01018](https://arxiv.org/abs/2508.01018)
- **de Vassimon Manela, Yang, Evans (2025), "Testing Generalizability in Causal Inference", UAI 2025 (PMLR v286).** Uses the frugal parameterization to build fully- and semi-synthetic benchmarks for mean and distributional regression methods. — [V] [PMLR](https://proceedings.mlr.press/v286/vassimon-manela25a.html)
- **Gentzel, Garant, Jensen (2019), "The Case for Evaluating Causal Models Using Interventional Measures and Empirical Data", NeurIPS.** Argues against purely synthetic evaluation and for interventional measures and empirical (e.g. RCT-subsampled) data. [S] — [arXiv 1910.05387](https://arxiv.org/abs/1910.05387)
- **Mahajan et al. (2024), "Empirical Analysis of Model Selection for Heterogeneous Causal Effect Estimation", ICLR 2024.** Large study of CATE model-selection metrics on RealCause-generated datasets. Relevance: choosing the evaluation and validation metric when there is no oracle. [S] — [arXiv 2211.01939](https://arxiv.org/abs/2211.01939)
- **"CausalBench"**: I could not pin down a single canonical "CausalBench" paper for treatment-effect estimation. Several unrelated works share the name (one is a single-cell causal-discovery benchmark). → see Gaps.

### Inferences
- The thesis pipeline (real IoT trace + specified outcome model + simulated historical policy) is IHDP/ACIC-style, with a RealCause-style option if the dynamics are fitted. Per Curth et al., the design choices themselves (outcome-model class, how overlap is induced) should be varied factorially rather than fixed. Otherwise the benchmark may favour the learner whose inductive bias matches the hand-coded outcome function, e.g. a threshold rule favouring tree or threshold policies.
- Credence and Frugal Flows show how to make **confounding strength an explicit knob**, including unobserved confounding. That fits a sensitivity sweep in which the historical stop policy depends on a latent sensor feature the learner cannot see.

### Gaps
- "CausalBench" for CATE: the name is ambiguous, and I could not verify a single paper.
- I did not open the Credence full text to confirm the exact generator architecture beyond the slides.

---

## 2. Benchmarks in process mining / PresPM

### Takeaway
The KU Leuven group (De Moor, Weytjens, De Smedt, De Weerdt) dominates benchmark-oriented PresPM. SimBank (a fully synthetic simulator with oracle counterfactuals, including sequential interventions) came first, then ProCause (counterfactuals generated from real logs, RealCause-style), then SCOPE (sequential causal backward induction plus a reusable semi-synthetic benchmark on a real log). The search found no PresPM benchmark built on IoT/sensor-enriched logs, and none that studies decision points at arbitrary sensor readings rather than events. That suggests a genuine novelty gap.

### Cited Findings (annotated list)
- **De Moor, Weytjens, De Smedt, De Weerdt (2025), "SimBank: from Simulation to Solution in Prescriptive Process Monitoring", arXiv 2506.14772 (v1 Mar 2025, v3 Jul 2025).** Simulator of a bank loan-application process with parallel activities and loops. It generates the true outcome under every intervention for each test case, and defines three intervention problems of increasing complexity, including sequential intervention strategies, which the authors call underexplored. It compares four PresPM methods and supports offline and online training. — [V] [arXiv](https://arxiv.org/abs/2506.14772)
- **De Moor, Weytjens, De Smedt (2025), "ProCause: Generating Counterfactual Outcomes to Evaluate Prescriptive Process Monitoring Methods", arXiv 2509.00797. OpenAlex lists it at ICPM 2025 (DOI 10.1109/ICPM66919.2025.11220278).** Generates counterfactual outcomes for real logs using sequential (LSTM) or non-sequential base models in S-Learner, T-Learner and TARNet architectures, plus an ensemble that averages the three. It is validated with a real-data analysis. RL is explicitly left out of scope because it "typically requires online learning". Note: the thesis repo already contains ProClause/ProCause as a submodule. — [V] [arXiv](https://arxiv.org/abs/2509.00797); [OpenAlex record](https://api.openalex.org/works/doi:10.1109%2FICPM66919.2025.11220278)
- **De Moor, Weytjens, De Smedt, De Weerdt (2025/2026), "SCOPE: Sequential Causal Optimization of Process Interventions", arXiv 2512.17629 (v1 19 Dec 2025, v4 9 Jun 2026).** Recommends *sequences* of interventions by backward induction (from the last decision point to the first) with causal learners applied directly to observational data. This avoids building a process simulator for RL, which the authors argue creates a reality gap and bias. It introduces a reusable semi-synthetic benchmark on a real-life event log, and the authors report that it beats state-of-the-art PresPM methods on SimBank and on the new benchmark. Relevance: **the closest prior work to the thesis** (sequential decisions, semi-synthetic, offline). The thesis must position against it. — [V] [arXiv](https://arxiv.org/abs/2512.17629)
- **Weytjens, Verbeke, De Weerdt (2023), "Timing Process Interventions with Causal Inference and Reinforcement Learning", arXiv 2306.04299 (BPM-workshop/ICPM-era).** Quantitative comparison of causal inference and online RL for *when* to intervene, on synthetic data where ground truth is available. Relevance: timing is the same as start/stop decisions. — [V] [arXiv](https://arxiv.org/abs/2306.04299)
- **Bozorgi, Dumas, La Rosa, Polyvyanyy, Shoush, Teinemaa (2023), "Learning When to Treat Business Processes: Prescriptive Process Monitoring with Causal Inference and Reinforcement Learning", arXiv 2303.03572 (CAiSE 2023).** Combines causal-forest uplift estimates with RL to decide when to treat under resource limits. [V, title/link only] — [arXiv](https://arxiv.org/abs/2303.03572)
- **Shoush & Dumas (2022), "Intervening With Confidence: Conformal Prescriptive Monitoring of Business Processes", arXiv 2212.03710.** Learns intervention policies offline from past data with conformal guarantees, under limited resources. — [V] [arXiv](https://arxiv.org/abs/2212.03710)
- **Offline-RL PresPM with "alternative outcomes" (2023).** The search summary describes a paper that augments the event log with alternative outcomes so an RL agent can learn timing offline. I could not confirm the exact paper or its authors. — [V, partial] cited via [Springer chapter link from search](https://springerlink.bibliotecabuap.elogim.com/10.1007/978-3-031-50974-2_19) (mirror URL; check against the official Springer DOI 10.1007/978-3-031-50974-2_19)
- **Abbasi et al. (2025), "FORLAPS"**: offline RL fine-tuned for next-activity recommendation, with process-aware data augmentation. — [V] [arXiv 2501.10543](https://arxiv.org/abs/2501.10543)
- **Kubrak, Milani, Nolte, Dumas (2022), "Prescriptive process monitoring: Quo vadis?", PeerJ Computer Science.** Systematic review of PresPM. It notes that evaluation is heterogeneous and that ground truth is scarce. [S] — [arXiv 2112.01769](https://arxiv.org/abs/2112.01769)
- **IoT-enriched logs (data substrate, not PresPM):**
  - Malburg et al. (2022), "An IoT-Enriched Event Log for Process Mining in Smart Factories". — [V] [arXiv 2209.02702](https://arxiv.org/abs/2209.02702)
  - Mangler et al.? (2022), "SensorStream: An XES Extension for Enriching Event Logs with IoT-Sensor Data". The author list was not checked. — [V] [arXiv 2206.11392](https://arxiv.org/abs/2206.11392)
  - The search summary says that abstracting fine-grained IoT data into classical XES/OCEL "considerably limits analysis possibilities". That supports keeping the raw time series, as in the thesis's "decision at arbitrary sensor readings" RQ. — [V] via [arXiv 2209.02702](https://arxiv.org/abs/2209.02702) search snippet

### Inferences
- **Novelty check:** SimBank, ProCause and SCOPE all decide at *event* boundaries on business-process logs. None of them treats sub-event sensor-reading granularity or IoT signals. A semi-synthetic PresPM benchmark built from an IoT log, comparing event-aligned and sensor-aligned decision points, appears unaddressed in the work found. Confidence is moderate, because the search covered arXiv/Google-indexed works only.
- SCOPE's argument against RL (that simulators create a reality gap) mirrors the thesis's signal-replay bias issue. The thesis can frame "signal replay vs fitted dynamics" as an empirical test of exactly that claim.

### Gaps
- I did not obtain SCOPE's benchmark construction details (outcome model, historical policy, overlap handling) from the abstract page. Read the full HTML: https://arxiv.org/html/2512.17629
- No "Benchmarking PresPM" survey paper with a leaderboard was found beyond SimBank.

---

## 3. Semi-synthetic / simulated benchmarks for time-series treatment effects and causal discovery

### Takeaway
Longitudinal treatment-effect work still relies on two testbeds: the PK-PD **tumour-growth simulator** (Geng et al. 2017; used in RMSN, CRN, Causal Transformer) and **semi-synthetic MIMIC-III** (real vitals, simulated treatments and outcomes; Melnychuk et al. 2022). For causal discovery, CausalTime (ICLR 2024) fits neural dynamics with normalizing flows to real series. The time-confounding knob (gamma) in the tumour simulator is the standard way to sweep confounding strength over time.

### Cited Findings (annotated list)
- **Bica, Alaa, Jordon, van der Schaar (2020), "Estimating Counterfactual Treatment Outcomes over Time Through Adversarially Balanced Representations" (CRN), ICLR.** Uses the tumour-growth PK-PD simulator with a parameter gamma that controls time-dependent confounding. The historical treatment probability is a sigmoid of the recent tumour diameter. Relevance: a direct template for a "historical policy depends on the recent signal" design with a tunable confounding strength. [S] — [arXiv 2002.04083](https://arxiv.org/abs/2002.04083)
- **Lim, Alaa, van der Schaar (2018), "Forecasting Treatment Responses Over Time Using Recurrent Marginal Structural Networks" (RMSN), NeurIPS.** First deep model on the tumour simulator. Uses IPTW over time. [S] — [NeurIPS proceedings](https://proceedings.neurips.cc/paper/2018/hash/56e6a93212e4482d99c84a639d254b67-Abstract.html)
- **Melnychuk, Frauen, Feuerriegel (2022), "Causal Transformer for Estimating Counterfactual Outcomes", ICML.** Introduces the semi-synthetic MIMIC-III benchmark (real covariates, simulated treatments and outcomes). The repo notes a bug in the synthetic tumour-growth simulator that affects earlier results, which is a warning about simulator bugs propagating through a literature. — [V] repo: [github.com/Valentyn1997/CausalTransformer](https://github.com/Valentyn1997/CausalTransformer); paper [S] [arXiv 2204.07258](https://arxiv.org/abs/2204.07258)
- **COSTAR (2023), arXiv 2311.00886.** Confirms that tumour growth plus semi-synthetic MIMIC-III is "the common evaluation setup". — [V] [arXiv](https://arxiv.org/abs/2311.00886)
- **DeepBlip (2025), "Estimating Conditional Average Treatment Effects Over Time", arXiv 2511.14545.** Extends semi-synthetic MIMIC with time-decaying effects and reports that this makes estimation harder than earlier benchmarks. — [V] [arXiv](https://arxiv.org/abs/2511.14545)
- **Cheng, Wang, Xiao, Zhong, Suo, He (2024), "CausalTime: Realistically Generated Time-series for Benchmarking of Causal Discovery", ICLR 2024.** Fits deep networks plus normalizing flows to real multivariate series, extracts a hypothesised graph, and splits the model into causal, residual and noise terms to get the ground truth. Fidelity is checked qualitatively and quantitatively. The authors argue that purely synthetic data cannot predict performance on real data. Relevance: a recipe for **fitted-dynamics generation from real sensor data with checked fidelity**, i.e. the alternative to signal replay. — [V] [arXiv 2310.01753](https://arxiv.org/abs/2310.01753); [ICLR proceedings](https://proceedings.iclr.cc/paper_files/paper/2024/hash/0c79d6ed1788653643a1ac67b6ea32a7-Abstract-Conference.html)
- **Van den Bulcke et al. (2006), "SynTReN: a generator of synthetic gene expression data for design and analysis of structure learning algorithms", BMC Bioinformatics.** Generates synthetic data from real network topologies. Relevance to the thesis is low (gene networks); it is listed only because the brief asked for it. [S] — [DOI 10.1186/1471-2105-7-43](https://doi.org/10.1186/1471-2105-7-43)
- **Digital twins as evaluation environments:** no specific benchmark paper was verified. → Gaps.

### Inferences
- CRN's gamma is the simplest defensible way to parameterise the **confounding strength of the simulated historical stop policy**, e.g. P(stop at t) = sigmoid(gamma · (signal_t − threshold)). Sweeping gamma from 0 (random, high overlap) up to large values (near-deterministic, low overlap) separates the overlap problem from learner quality.
- CausalTime and the Causal Transformer bug together show that a fitted-dynamics benchmark needs (a) fidelity tests (discriminator or two-sample tests, as in RealCause and CausalTime) and (b) published simulator code with unit tests.

### Gaps
- No verified "digital twin as benchmark for prescriptive/causal methods" paper was found. That would need a dedicated search.

---

## 4. Offline RL and off-policy evaluation (OPE): methods, benchmarks, coverage/pessimism

### Takeaway
Offline RL theory says learnability depends on **coverage (concentrability)** of the target policy by the behaviour data. Pessimism (CQL, IQL-style in-sample learning, BCQ constraints, LCB-based methods) is the main fix. In practice, on near-real-world benchmarks such as NeoRL and NeoRL-2, methods built from conservative controllers' data often *fail to beat the behaviour policy*. This is exactly the thesis's low-overlap situation (the historical policy mostly stops at window end).

### Cited Findings (annotated list)
**Tutorials / theory**
- **Levine, Kumar, Tucker, Fu (2020), "Offline Reinforcement Learning: Tutorial, Review, and Perspectives on Open Problems", arXiv.** Frames distributional shift as the core problem, and covers policy constraints, conservative values, model-based methods and OPE. [S] — [arXiv 2005.01643](https://arxiv.org/abs/2005.01643)
- **Chen & Jiang (2019), "Information-Theoretic Considerations in Batch Reinforcement Learning", ICML.** Formalises concentrability and shows that batch RL needs data coverage plus a realizable, complete function class. [S] — [arXiv 1905.00360](https://arxiv.org/abs/1905.00360)
- **Jin, Yang, Wang (2021), "Is Pessimism Provably Efficient for Offline RL?", ICML.** Pessimistic value iteration has suboptimality bounded by coverage of the *optimal* policy only. [S] — [arXiv 2012.15085](https://arxiv.org/abs/2012.15085)
- **Rashidinejad, Zhu, Ma, Jiao, Russell (2021), "Bridging Offline RL and Imitation Learning: A Tale of Pessimism", NeurIPS.** Introduces the single-policy concentrability coefficient C*. LCB-based pessimism adapts to data quality, from expert (imitation) data to uniform data. [S] — [arXiv 2103.12021](https://arxiv.org/abs/2103.12021)

**Algorithms**
- **Fujimoto, Meger, Precup (2019), "Off-Policy Deep RL without Exploration" (BCQ), ICML.** Constrains actions to those the behaviour policy supports. [S] — [arXiv 1812.02900](https://arxiv.org/abs/1812.02900)
- **Kumar, Zhou, Tucker, Levine (2020), "Conservative Q-Learning for Offline RL" (CQL), NeurIPS.** Penalises Q-values of out-of-distribution actions, giving a lower bound on the policy value. [S] — [arXiv 2006.04779](https://arxiv.org/abs/2006.04779)
- **Kostrikov, Nair, Levine (2021/22), "Offline RL with Implicit Q-Learning" (IQL), ICLR 2022.** Expectile regression with in-sample learning that never queries unseen actions. A strong, simple baseline. [S] — [arXiv 2110.06169](https://arxiv.org/abs/2110.06169)
- **Model-based offline RL (fitted dynamics with an uncertainty penalty): MOPO (Yu et al. 2020) and MOReL (Kidambi et al. 2020).** Relevance: their uncertainty-penalised learned dynamics are the RL counterpart of the thesis's "fitted dynamics vs signal replay" choice. [S] — [MOPO arXiv 2005.13239](https://arxiv.org/abs/2005.13239); [MOReL arXiv 2005.05951](https://arxiv.org/abs/2005.05951)

**OPE**
- **Le, Voloshin, Yue (2019), "Batch Policy Learning under Constraints", ICML.** Introduces and analyses Fitted Q Evaluation (FQE). [S] — [arXiv 1903.08738](https://arxiv.org/abs/1903.08738)
- **Jiang & Li (2016), "Doubly Robust Off-policy Value Evaluation for RL", ICML.** Sequential DR estimator. [S] — [arXiv 1511.03722](https://arxiv.org/abs/1511.03722)
- **Thomas & Brunskill (2016), "Data-Efficient Off-Policy Policy Evaluation for RL" (WDR/MAGIC), ICML.** [S] — [arXiv 1604.00923](https://arxiv.org/abs/1604.00923)
- **Voloshin, Le, Jiang, Yue (2019/2021), "Empirical Study of Off-Policy Policy Evaluation for RL" (COBS), NeurIPS D&B 2021.** Gives practical guidance: no estimator dominates, and horizon length and policy mismatch decide which family works (IS-based vs direct/FQE vs hybrid). [S] — [arXiv 1911.06854](https://arxiv.org/abs/1911.06854)
- **Fu et al. (2021), "Benchmarks for Deep Off-Policy Evaluation" (DOPE), ICLR.** Finds FQE competitive, and shows OPE often fails at ranking policies under large distribution shift. [S] — [arXiv 2103.16596](https://arxiv.org/abs/2103.16596)
- **Paine et al. (2020), "Hyperparameter Selection for Offline RL", arXiv.** OPE (FQE) for model selection. [S] — [arXiv 2007.09055](https://arxiv.org/abs/2007.09055)
- **Tang & Wiens (2021), "Model Selection for Offline RL: Practical Considerations for Healthcare Settings", MLHC.** [S] — [arXiv 2107.11003](https://arxiv.org/abs/2107.11003)
- **Uehara, Shi, Kallus (2022), "A Review of Off-Policy Evaluation in Reinforcement Learning", arXiv.** Statistical review covering efficiency and DR estimators. [S] — [arXiv 2212.06355](https://arxiv.org/abs/2212.06355)
- **Saito et al. (2021), "Open Bandit Dataset and Pipeline", NeurIPS D&B.** Real logged-bandit data with two policies, which makes it possible to *validate OPE against a real on-policy value*. Relevance: a design idea for validating benchmark OPE. [S] — [arXiv 2008.07146](https://arxiv.org/abs/2008.07146)

**Benchmarks**
- **Fu, Kumar, Nachum, Tucker, Levine (2020), "D4RL: Datasets for Deep Data-Driven RL", arXiv.** Behaviour data of varying quality (random, medium, medium-replay, expert) on MuJoCo/AntMaze. The "dataset quality" axis is a useful template. [S] — [arXiv 2004.07219](https://arxiv.org/abs/2004.07219)
- **Gulcehre et al. (2020), "RL Unplugged", NeurIPS.** [S] — [arXiv 2006.13888](https://arxiv.org/abs/2006.13888)
- **Qin et al. (2021/2022), "NeoRL: A Near Real-World Benchmark for Offline RL", NeurIPS D&B 2022.** Data from conservative, deterministic-ish deployed-style policies, limited data, and an industrial benchmark task. It advocates offline policy validation before deployment. [S] — [arXiv 2102.00714](https://arxiv.org/abs/2102.00714)
- **Gao, Tu, Qin, Sun, Chen, Yu (2025), "NeoRL-2: Near Real-World Benchmarks for Offline RL with Extended Realistic Scenarios", arXiv 2503.19267.** Seven tasks with simulators that model *extremely conservative data from deployed control systems*, delayed action effects and uncontrollable external factors. Data are sampled with deterministic methods. **Current methods often struggle to outperform the data-collection behaviour policy.** Code: github.com/polixir/NeoRL2. — [V] [arXiv](https://arxiv.org/abs/2503.19267)
- **Hein et al. (2017), "A Benchmark Environment Motivated by Industrial Control Problems" (Industrial Benchmark), IEEE SSCI 2017.** Siemens. High-dimensional, heteroscedastic, partially observable dynamics meant to capture the general character of turbine-like control without imitating a specific plant. Java/Python code with a Gym wrapper (github.com/siemens/industrialbenchmark). — [V] [arXiv 1709.09480](https://arxiv.org/abs/1709.09480)
- **Hein et al. (2017), "Batch Reinforcement Learning on the Industrial Benchmark: First Experiences".** PSO-policy vs NFQ vs recurrent control nets in the batch setting. — [V] [arXiv 1705.07262](https://arxiv.org/abs/1705.07262)
- **PC-Gym (2024), "Benchmark Environments for Process Control Problems".** Chemical process-control RL environments with disturbances and constraints. Online, not offline. — [V] [arXiv 2410.22093](https://arxiv.org/abs/2410.22093)
- **Durkin et al. (2025), offline RL for chemical process control ("Safe Deployment of Offline RL via Input Convex Action Correction").** Releases offline datasets from PI controllers with randomised tunings. BC and IQL baselines struggle with steady-state offsets near setpoints. — [V, summary only] The link came from the search result list and was not opened: [arXiv 2507.22640](https://arxiv.org/abs/2507.22640)
- **Bloor et al. (2025), "A Survey and Tutorial of RL Methods in Process Systems Engineering".** — [V] [arXiv 2510.24272](https://arxiv.org/abs/2510.24272)

### Inferences
- In the thesis's low-overlap setting ("historical policy mostly stops at window end"), the policy "stop early when the signal is X" has almost no support. Single-policy concentrability C* is effectively infinite for the optimal policy, so no offline method can be expected to learn it reliably. Pessimistic methods (CQL, IQL) will correctly fall back to "stop at end". Benchmark design should therefore (a) report a coverage or overlap statistic per decision point, and (b) include behaviour policies of varying stochasticity, as D4RL varies dataset quality and the CRN gamma sweep varies confounding.
- NeoRL-2's finding (methods fail to beat a conservative behaviour policy) is a realistic baseline expectation. **The behaviour policy and "stop at end" belong in the results table as baselines.**
- For OPE inside the benchmark: the oracle exists, so OPE estimators (FQE, DR, WIS) can themselves be *evaluated* against the oracle, which is a contribution in its own right. COBS/DOPE say no estimator dominates, so report several.

### Gaps
- Offline RL specifically for discrete manufacturing or food-process machines (such as the cotton candy machine) did not show up. Process-control work is mostly continuous chemical control.

---

## 5. Dynamic treatment regimes, optimal stopping and confounded / causal offline RL

### Takeaway
Start/stop decisions are a special case of dynamic treatment regimes (DTRs) and are well studied in statistics and econometrics. Q-learning with backward induction (Murphy), A-learning, outcome-weighted learning (OWL), and *when-to-treat* policy learning (Nie, Brunskill, Wager 2020) are natural, theory-backed baselines that predate deep offline RL. SCOPE's backward induction is in effect DTR Q-learning applied to process mining.

### Cited Findings (annotated list)
- **Murphy (2003), "Optimal Dynamic Treatment Regimes", JRSSB.** Semiparametric approach to multi-stage regimes (the A-learning lineage). [S] — [DOI 10.1111/1467-9868.00389](https://doi.org/10.1111/1467-9868.00389)
- **Murphy (2005), "A Generalization Error for Q-Learning", JMLR.** [S] — [JMLR](https://www.jmlr.org/papers/v6/murphy05a.html)
- **Zhao, Zeng, Rush, Kosorok (2012), "Estimating Individualized Treatment Rules Using Outcome Weighted Learning", JASA.** Recasts policy learning as weighted classification. [S] — [DOI 10.1080/01621459.2012.695674](https://doi.org/10.1080/01621459.2012.695674)
- **Zhao, Zeng, Laber, Kosorok (2015), "New Statistical Learning Methods for Estimating Optimal Dynamic Treatment Regimes" (BOWL/SOWL), JASA.** Multi-stage OWL. [S] — [DOI 10.1080/01621459.2014.937488](https://doi.org/10.1080/01621459.2014.937488)
- **Chakraborty & Moodie (2013), "Statistical Methods for Dynamic Treatment Regimes", Springer.** Book covering Q-learning, A-learning, G-estimation and inference. [S] — [DOI 10.1007/978-1-4614-7428-9](https://doi.org/10.1007/978-1-4614-7428-9)
- **Nie, Brunskill, Wager (2021), "Learning When-to-Treat Policies", JASA 116(533).** Doubly robust policy learning for *when to start (or stop)* treatment from observational data, with regret bounds and no Markov assumption. **Directly applicable to start/stop decisions in the thesis.** — [V] [arXiv 1905.09751](https://arxiv.org/abs/1905.09751)
- **"Policy Learning for Optimal Dynamic Treatment Regimes with Observational Data" (2024), arXiv 2404.00221.** Frames optimal stopping and starting as a constrained DTR class under sequential ignorability. Example: unemployment-insurance cutoffs. — [V] [arXiv](https://arxiv.org/abs/2404.00221)
- **"Learning to search efficiently for causally near-optimal treatments" (2020), arXiv 2007.00973.** Treats stopping as an action, learned from observational data with censoring. — [V] [arXiv](https://arxiv.org/abs/2007.00973)
- **Kallus & Zhou (2018), "Confounding-Robust Policy Learning", NeurIPS.** Minimax-regret policy learning under a marginal-sensitivity model of unobserved confounding. [S] — [arXiv 1805.08593](https://arxiv.org/abs/1805.08593)
- **Namkoong, Keramati, Yadlowsky, Brunskill (2020), "Off-policy Policy Evaluation For Sequential Decisions Under Unobserved Confounding", NeurIPS.** Shows that OPE bounds blow up even when confounding is limited to one time step. [S] — [arXiv 2003.05623](https://arxiv.org/abs/2003.05623)
- **Gottesman et al. (2019), "Guidelines for reinforcement learning in healthcare", Nature Medicine.** Practical warnings: confounding, effective sample size under IS, and checking whether learned policies just exploit artifacts. [S] — [DOI 10.1038/s41591-018-0310-5](https://doi.org/10.1038/s41591-018-0310-5)

### Inferences
- For a stop/continue problem with few decision points, fitted Q-iteration / DTR Q-learning (backward induction), the Nie-Brunskill-Wager DR when-to-treat learner, and SCOPE are the right "causal" baselines next to CQL/IQL. That keeps the comparison from being deep-RL-only.
- The RQ on decision granularity (arbitrary sensor readings vs events) changes the horizon length. Longer horizons hurt IS-based OPE exponentially (COBS) and increase per-step overlap problems. That is a concrete, testable mechanism by which finer granularity may *hurt* offline learning despite carrying more information.

### Gaps
- Zhang & Bareinboim's causal RL work (MDPUC, confounded MDPs) was not checked in this session.

---

## 6. Policy-learning baselines and overlap diagnostics / remedies

### Takeaway
Simple interpretable baselines (threshold rules, depth-limited policy trees from doubly robust scores) are strong and should always be included. With low overlap, the established tools are diagnosis (propensity histograms, effective sample size, overlap-weighted estimands), trimming or overlap weights (Crump et al.; Li, Morgan, Zaslavsky), and restricting the policy class or estimand to the region of support. D'Amour et al. show that strict overlap becomes implausible in high-dimensional covariates, which is directly relevant to rich sensor features.

### Cited Findings (annotated list)
- **Athey & Wager (2021), "Policy Learning With Observational Data", Econometrica.** Doubly robust (AIPW) scores plus empirical welfare maximisation over a restricted class, with sqrt(n) regret bounds. [S] — [arXiv 1702.02896](https://arxiv.org/abs/1702.02896)
- **Zhou, Athey, Wager (2023), "Offline Multi-Action Policy Learning: Generalization and Optimization", Operations Research.** Tree-based policies with an exact search algorithm (the `policytree` R package). [S] — [arXiv 1810.04778](https://arxiv.org/abs/1810.04778)
- **D'Amour, Ding, Feller, Lei, Sekhon (2021), "Overlap in observational studies with high-dimensional covariates", J. Econometrics.** Strict overlap implies bounded mean discrepancy between treated and control covariate distributions. As dimension grows, that becomes very restrictive, so many high-dimensional analyses implicitly violate it. Remedies include dimension reduction of the conditioning set and changing the estimand. [S] — [arXiv 1711.02582](https://arxiv.org/abs/1711.02582)
- **Crump, Hotz, Imbens, Mitnik (2009), "Dealing with limited overlap in estimation of average treatment effects", Biometrika.** Optimal propensity trimming, with the rule of thumb of keeping 0.1 ≤ e(x) ≤ 0.9. [S] — [DOI 10.1093/biomet/asn055](https://doi.org/10.1093/biomet/asn055)
- **Li, Morgan, Zaslavsky (2018), "Balancing Covariates via Propensity Score Weighting" (overlap weights), JASA.** Targets the population with the most overlap. [S] — [DOI 10.1080/01621459.2016.1260466](https://doi.org/10.1080/01621459.2016.1260466)

### Inferences
- **Practical lessons for benchmark design (synthesis):**
  1. *Validity:* treat the simulator as a model of the data. Run fidelity tests of the generated sensor trajectories against held-out real ones (two-sample/discriminator tests as in RealCause and CausalTime), and publish the simulator code and seeds. The Causal Transformer bug shows why.
  2. *Overlap:* make behaviour-policy stochasticity an explicit factor (e.g. epsilon-mix or temperature on the stop rule). Report per-decision-point propensity ranges and the effective sample size of IS weights. Evaluate both on the full population and on an overlap-restricted subpopulation.
  3. *Confounding strength:* parameterise the historical policy's dependence on the signal (CRN-style gamma), and optionally on an *unobserved* latent (Frugal Flows / Kallus-Zhou style) to test robustness.
  4. *Realism / anti-favouritism:* vary the outcome-model class (threshold, smooth, interaction) so the benchmark does not favour the learner matched to the DGP (Curth et al.). Report rankings across settings, not single wins.
  5. *Signal-replay bias:* replaying the observed trace after an intervention assumes the action does not change future sensor values. That holds for pure stopping, but not for actions that alter the process. Fitted dynamics (MOPO/MOReL-style or CausalTime-style) relax the assumption but add model error. Run both and treat the difference as a sensitivity result.
  6. *Baselines:* the behaviour policy, "stop at end", the best constant-time stop, the oracle-tuned threshold policy, a policy tree on DR scores, DTR Q-learning/FQI, SCOPE, IQL and CQL.
  7. *Evaluation:* use oracle value and regret as the primary metrics. Evaluate OPE estimators (FQE, DR, WIS) against the oracle as a secondary contribution. Run multiple seeds and simulator replications and report confidence intervals.

### Gaps
- I found no work that systematically studies *decision-point granularity* (event vs time-step vs sensor-sample) for offline policy learning in process mining. This is a likely novelty, but absence of evidence comes from a limited search.
- Overlap diagnostics designed specifically for *sequential* (per-step) settings are scattered. Beyond effective sample size and C*, no canonical reference was verified.
