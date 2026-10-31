# Prescriptive analytics, causal inference and data-driven process control in manufacturing / IIoT (intervention timing and process-parameter decisions from sensor streams)

Verification legend:
- **[V]** = I opened the landing page or abstract during this session, or a search result returned the bibliographic record (title, venue, DOI) directly.
- **[S]** = secondhand. Taken from search snippets or citing works, or from prior knowledge with a DOI link that I did not open this session. Check before citing.

Scope note: this covers the manufacturing, OR and process-control community only. Process-mining-side PresPM work belongs to other researchers. Search covered literature up to Oct 2026, but searches were limited to about 20 calls, so this list is broad but **not exhaustive**.

---

## 1. Prescriptive analytics in manufacturing / Industry 4.0: reviews and foundations

### Takeaway
The reviews treat prescriptive analytics as the least mature analytics type. They classify it by method (optimisation, simulation, ML/RL) and by system archetype (advisory to self-governing). None of the reviews found treats *when* to decide (decision-point timing within a running case or sensor stream) as its own design dimension.

### Cited Findings (annotated list)
- **Lepenioti, Bousdekis, Apostolou, Mentzas (2020). "Prescriptive analytics: Literature review and research challenges." *Int. J. Information Management* 50:57–70. DOI 10.1016/j.ijinfomgt.2019.04.003. [V, abstract only]**
  - Summary: reviews prescriptive analytics methods (mathematical programming, evolutionary, simulation, probabilistic models, ML) and lists research challenges. It treats prescriptive analytics as the least mature of descriptive, predictive and prescriptive analytics.
  - Relevance: the standard citation for defining prescriptive analytics. Bousdekis and Mentzas come from predictive maintenance and manufacturing.
  - Gap: I did not retrieve the full list of challenges.
  - Link: [IDEAS/RePEc](https://ideas.repec.org/a/eee/ininma/v50y2020icp57-70.html)
- **Wissuchek & Zschech (2024/2025). "Prescriptive analytics systems revised: a systematic literature review from an information systems perspective." *Information Systems and e-Business Management* 23(2), open access. [V, abstract]**
  - Summary: systematic review of 262 articles. It derives 23 components of prescriptive analytics systems (PAS) and 4 archetypes (advisory, executive, adaptive, self-governing), plus 6 research directions.
  - Relevance: gives the thesis a vocabulary to position its policy. A start/stop spinning policy acting on sensor readings is an "executive/adaptive" PAS.
  - Note: the 2023 ECIS predecessor uses slightly different archetype names (informative, executive, adaptive, autonomous).
  - Links: [FAU open](https://open.fau.de/handle/openfau/37693); [ECIS 2023 version](https://aisel.aisnet.org/ecis2023_rp/289)
- **Bertsimas & Kallus (2020). "From Predictive to Prescriptive Analytics." *Management Science* 66(3):1025–1044. DOI 10.1287/mnsc.2018.3253. [V]**
  - Summary: combines ML (kNN, kernel, tree and forest weights) with optimisation to map covariates to decisions. It introduces the "coefficient of prescriptiveness" P, an R² analogue for decisions.
  - Results: shown to be asymptotically optimal even for non-i.i.d. or censored data. On an inventory case it gave an 88% improvement in P.
  - Relevance: foundational for one-shot contextual decisions. It is *not sequential* and does not address timing.
  - Link: [arXiv 1402.5481](https://arxiv.org/abs/1402.5481)
- **Vater, Harscheidt, Knoll (2019). "Smart Manufacturing with Prescriptive Analytics: A review of the current status and future work." IEEE ICITM 2019. [S, seen via a Scribd copy]**
  - Summary: reviews prescriptive analytics in manufacturing. It proposes a framework for proactive, autonomous production control and structures approaches by level of human interaction and IT infrastructure.
  - Relevance: manufacturing-specific prescriptive analytics framing.
  - Note: I found no Procedia CIRP paper by Vater. The IEEE record was not opened.
  - Link: [Scribd copy](https://www.scribd.com/document/517884064/vater2019)
- **Weller, Dumitrescu et al. (2024). "Design decisions for integrating Prescriptive Analytics Use Cases into Smart Factories." *Procedia CIRP* 128:424–429. DOI 10.1016/j.procir.2024.03.022. [S]**
  - Summary: design decisions for deploying prescriptive analytics use cases in production. Related to the FUSE framework (MDPI *Electronics* 2025) for planning and integrating prescriptive analytics solutions.
  - Relevance: an engineering and integration view; no learning of timing policies.
  - Links: [Bohrium record](https://www.bohrium.com/paper-details/design-decisions-for-integrating-prescriptive-analytics-use-cases-into-smart-factories/1063132705341833262-28909); [MDPI Electronics 14(21):4271](https://www.mdpi.com/2079-9292/14/21/4271)
- **"Data-Driven Prescriptive Analytics Applications: A Comprehensive Survey" (2024). arXiv 2412.00034. [S]**
  - Summary: a recent cross-domain survey of prescriptive analytics applications. It takes its method categories from Lepenioti et al. 2020.
  - Link: [arXiv](https://arxiv.org/html/2412.00034v1)
- **Panzer & Bender (2022). "Deep reinforcement learning in production systems: a systematic literature review." *Int. J. Production Research* 60(13). DOI 10.1080/00207543.2021.1973138. [S, prior knowledge, link not opened]**
  - Summary: systematic review of deep RL in production, which is dominated by scheduling, dispatching and robotics.
  - Relevance: shows that RL in production mostly targets discrete-event decisions such as dispatching, not continuous-time process decisions.
  - Link: [DOI](https://doi.org/10.1080/00207543.2021.1973138)

### Inferences
- Prescriptive analytics reviews in manufacturing classify by *method* and *autonomy level*. Decision timing, and the granularity at which decisions are allowed, is not a recognised axis. That supports the thesis framing that granularity versus learnability is under-studied.

### Gaps
- I did not retrieve the full challenge lists of Lepenioti 2020 or Wissuchek & Zschech, so I cannot say whether either mentions "timing" explicitly.

---

## 2. Causal inference on manufacturing process data

### Takeaway
Causal work in manufacturing is mostly **causal discovery and root-cause analysis**. A small, recent strand (2023–2025) does **causal policy learning** for static decisions (rework yes/no, process-parameter setting). I found no causal work in manufacturing that estimates effects of *intervention timing* along a sensor trajectory.

### Cited Findings (annotated list)
- **Vuković & Thalmann (2022). "Causal Discovery in Manufacturing: A Structured Literature Review." *J. Manufacturing and Materials Processing* 6(1):10. DOI 10.3390/jmmp6010010. [V, DOAJ record]**
  - Summary: causal discovery is established in medicine, genetics and ecology, but applications in manufacturing are scattered and experimental. The review maps motivations, scenarios, approaches and implementation challenges.
  - Relevance: shows manufacturing causality is mostly about *structure learning*, not treatment-effect or policy estimation.
  - Link: [DOAJ](https://doaj.org/article/c82fc8b4147549c8b388b52c7657cc26)
- **Vuković (2025). PhD thesis "Causal Discovery in Industrial Data Analysis: A Framework for Trustworthy Industrial Intelligence." TU Graz, defended 18 July 2025. [S]**
  - Summary: case studies in steel and plastic injection moulding.
  - Link: [Pro2Future](https://www.pro2future.at/?p=13153)
- **Choudhary, Vuković et al. (2024). Causal discovery for monitoring process degradation in viscose fibre production. *Sensors* 24(12):3728. DOI 10.3390/s24123728. [S]**
  - Summary: causal graphs built with domain-expert background knowledge for process monitoring.
  - Link: [DOAJ](https://doaj.org/article/abb138360fbb4d3ea68833149e05c453)
- **Göbler et al. (2023). "causalAssembly: Generating realistic production data for benchmarking causal discovery." arXiv 2306.10816 (Bosch). [S]**
  - Summary: semi-synthetic benchmark generator from assembly-line data.
  - Relevance: a methodological parallel to the thesis' semi-synthetic benchmark (presbench/ccgen).
  - Link: [arXiv](https://arxiv.org/abs/2306.10816)
- **CausalMan (2025). "A physics-based simulator for large-scale causality." arXiv 2502.12707. [S]**
  - Summary: simulator for manufacturing causality benchmarks.
  - Relevance: another simulator-as-ground-truth precedent.
  - Link: [arXiv](https://arxiv.org/html/2502.12707v1)
- **Marazopoulou et al. (2016). Causal structure learning on production-line yield data. arXiv 1605.04056. [S]**
  - Link: [arXiv](https://arxiv.org/pdf/1605.04056v2.pdf)
- **Schwarz, Schacht, Klaassen, Grünbaum, Imhof, Spindler (2024). "Management Decisions in Manufacturing using Causal Machine Learning – To Rework, or not to Rework?" arXiv 2406.11308. [V, abstract]**
  - Summary: uses double/debiased ML to estimate lot-level conditional treatment effects of rework in multistage semiconductor (white LED colour-conversion) manufacturing, and derives rework policies.
  - Relevance: the closest manufacturing analogue to CATE-based PresPM. The decision point is fixed (before final inspection), *not timed*.
  - Conflict: the arXiv abstract reports a **2–3% yield improvement**. One search summary claimed "about 23%", which looks like a misreading. Use 2–3%.
  - Link: [arXiv](https://arxiv.org/abs/2406.11308)
- **Hung, Chen(?), Lee(?) (2025). "Robust and Interpretable Policy Learning for Manufacturing Process Parameters." *INFORMS J. Data Science*. DOI 10.1287/ijds.2024.0041. [S]**
  - Summary: frames process-parameter optimisation as causal policy learning with doubly robust policy-value estimation, tested on synthetic data and a real manufacturing case.
  - Relevance: a direct precedent for causal off-policy learning of process parameters. It appears to be a single-shot setting, not timing.
  - Author list unclear: search results gave "Yu-Hsin Hung" and "Bo-Ru …". The precursor is likely a 2023 NTU master's thesis by Bo-Ru Chen, advised by Chia-Yen Lee.
  - The publisher page returned 403, so this was not verified.
  - Link: [INFORMS](https://pubsonline.informs.org/doi/10.1287/ijds.2024.0041)

### Inferences
- The manufacturing causal-ML strand (Schwarz et al. 2024; IJDS 2025) does what PresPM does with CATE and uplift models: one treatment at one predetermined decision point. It does **not** handle continuous-time decision points or treatment-timing effects.
- Causal methods for "when to treat" exist in biostatistics (dynamic treatment regimes, treatment timing), but I found no manufacturing application. That is a candidate novelty gap; another researcher should check the biostatistics side.

### Gaps
- No manufacturing survey on *causal effect estimation* (as opposed to discovery) was found.
- I did not find the specific "Kuhnle / Lechner causal ML industrial" work the brief mentions. Andreas Kuhnle is known for **RL** in production control (see section 3), not causal ML. Lechner's causal ML work found here is econometrics (Knaus, Lechner, Strittmatter, [IZA DP 12039](https://docs.iza.org/dp12039.pdf)), not manufacturing.

---

## 3. RL for process control and adaptive production decisions

### Takeaway
RL for batch and chemical process control is an active area with reviews and offline-RL papers from 2021 to 2025. These works act at **every control interval** (fixed sampling time), which is effectively the "arbitrary sensor reading" granularity. They take the time grid as given, however, and do not study the effect of decision granularity on learnability, or compare event-aligned with sensor-aligned decision points.

### Cited Findings (annotated list)
- **Yoo, Byun, Han, Lee (2021). "Reinforcement learning for batch process control: Review and perspectives." *Annual Reviews in Control* 52:108–119. DOI 10.1016/j.arcontrol.2021.10.006. [V, record]**
  - Summary: reviews batch control (NMPC is the standard) and introduces RL for recipe optimisation and tracking control. It discusses application issues such as sample efficiency, safety and constraints.
  - Relevance: the main review for "batch process + RL". Cotton candy heating and spinning is a small batch process.
  - Link: [KAIST](https://koasas.kaist.ac.kr/handle/10203/291729)
- **Yoo, Kim, Kim, Lee (2021). "Reinforcement learning based optimal control of batch processes using Monte-Carlo deep deterministic policy gradient with phase segmentation." *Computers & Chemical Engineering* 144:107133. [V, PDF record]**
  - Summary: applies Monte-Carlo deep deterministic policy gradient (DDPG) with **phase segmentation** to a batch polyol polymerisation reactor and compares against NMPC.
  - Relevance: phase segmentation of a batch is conceptually close to the thesis' heating/spinning phases and to event-aligned decision points.
  - Link: [PDF](https://dspace.kaist.ac.kr/bitstream/10203/280027/1/1-s2.0-S0098135420307912-main.pdf)
- **Sobhani et al. (2024). Offline RL for a fed-batch chemical process (ESCAPE34/PSE24). [S]**
  - Summary: compares CQL, BCQ, IQL and behaviour cloning trained on historical batch data, with a reward designed to replicate optimal batches.
  - Relevance: offline RL from logged batch data, the same data regime as PresPM.
  - Link: [AIDIC](https://www.aidic.it/escape34-pse24/programma/629Sobhani.docx)
- **Wang, Kontoravdi, del Rio Chanona (2025). Offline RL for bioprocess optimisation (DYCOPS 2025). [S]**
  - Summary: trains on historical data and warns that naive offline Q-learning fails on out-of-distribution actions.
  - Link: [PDF](https://skoge.folk.ntnu.no/prost/proceedings/dycops-2025/DYCOPS2025_offline_program/contents/papers/0110.pdf)
- **Park, Shim, Lee (2023). "Offline Reinforcement Learning for Control of Complex Chemical Processes." AIChE Annual Meeting. [S]**
  - Summary: uses CQL and soft actor-critic (SAC). It notes that plants still rely on PID control and MPC.
  - Link: [AIChE](https://aiche.org/conferences/aiche-annual-meeting/2023/proceeding/paper/207a-offline-reinforcement-learning-control-complex-chemical-processes)
- **"A Survey and Tutorial of Reinforcement Learning Methods in Process Systems Engineering" (2025). arXiv 2510.24272. [S]**
  - Summary: recent survey and tutorial on RL in process systems engineering.
  - Link: [arXiv](https://arxiv.org/html/2510.24272)
- **Nian, Liu, Huang (2020). "A review on reinforcement learning: Introduction and applications in industrial process control." *Computers & Chemical Engineering* 139:106886. [S, prior knowledge]**
  - Link: [DOI](https://doi.org/10.1016/j.compchemeng.2020.106886)
- **Shin, Badgwell, Liu, Lee (2019). "Reinforcement Learning – Overview of recent progress and implications for process control." *Computers & Chemical Engineering* 127:282–294. [S, prior knowledge]**
  - Link: [DOI](https://doi.org/10.1016/j.compchemeng.2019.05.029)
- **Petsagkourakis, Sandoval, Bradford, Zhang, del Rio Chanona (2020). "Reinforcement learning for batch bioprocess optimization." *Computers & Chemical Engineering* 133:106649. [S, prior knowledge]**
  - Summary: policy gradient on a batch bioprocess with transfer from a model to the plant.
  - Link: [DOI](https://doi.org/10.1016/j.compchemeng.2019.106649)
- **Kuhnle, Kaiser, Theiß, Stricker, Lanza (2021). "Designing an adaptive production control system using reinforcement learning." *J. Intelligent Manufacturing* 32:855–876. [S, prior knowledge]**
  - Summary: RL for order dispatching in semiconductor production.
  - Relevance: RL at discrete-event decision points, the event-aligned analogue.
  - Link: [DOI](https://doi.org/10.1007/s10845-020-01612-y)
- **Kim et al. (2025). "DRL-Based Injection Molding Process Parameter Optimization for Adaptive and Profitable Production." arXiv 2505.10988. [S]**
  - Summary: SAC and PPO trained offline on surrogate models of quality and cycle time. The profit function includes resin, mould wear and **time-of-use electricity prices**. Reported to match genetic algorithms with up to 135x faster inference.
  - Relevance: high. It is the only paper found with a combined quality and energy-cost objective, similar to weight versus energy cost in the cotton candy case.
  - Link: [arXiv](https://arxiv.org/abs/2505.10988)
- **Injection moulding RL, other work [S]:**
  - Ren et al. (2024): enhanced TD3 with behaviour cloning. [XJTU](https://scholar.xjtu.edu.cn/zh/publications/autonomous-injection-molding-parameter-tuning-via-enhanced-td3-ba/)
  - Feng et al. (2025): Q-learning MDP for tuning. [J. GDUT](https://xbzrb.gdut.edu.cn/en/article/doi/10.12052/gdutxb.240142)
  - DFG project 548155694 on RL control of injection moulding, offline first and then on the machine. [GEPRIS](https://gepris.dfg.de/gepris/projekt/548155694)

### Inferences
- Process-control RL already makes decisions "at any sensor reading" (every sampling interval). The thesis therefore cannot claim novelty for acting at sensor granularity *per se* in the control sense.
- The thesis differs in three ways. Its data is **event-log plus sensor** data, not a state-space model. It uses **observational logged data with confounding**, whereas control RL usually assumes a simulator or a known model. And it explicitly **studies granularity as a variable**, comparing event-aligned and sensor-aligned decision points and measuring learnability trade-offs.
- Yoo et al.'s "phase segmentation" is the nearest thing to event-aligned decision points in process-control RL.

### Gaps
- I found no paper that systematically varies the control or decision interval and measures offline-RL learnability or sample efficiency in manufacturing. That should be confirmed by a targeted search on "action repetition / decision frequency / temporal abstraction" in the RL literature.
- I found no RL work on curing-time or thermal end-point control specifically (searches were limited).

---

## 4. Sensor-driven "when to stop" decisions: end-point detection, early termination, CBM timing, virtual metrology

### Takeaway
"When to stop" has long been handled in industry by **end-point detection** (rules, spectroscopy plus a classifier, soft sensors) and by **VM-enabled run-to-run control**. These are predict-then-threshold approaches, not learned policies with counterfactual evaluation. RL for maintenance timing frames the problem as an MDP or optimal stopping problem, but uses simulated degradation models.

### Cited Findings (annotated list)
- **Mählkvist, Ejenstam, Kyprianidis (2023). "Cost-Sensitive Decision Support for Industrial Batch Processes." *Sensors* 23(23):9464. [V, full text]**
  - Summary: at Kanthal thermocouple alloy production (119 melt batches, 1,049 sub-batches), predicts whether a batch will be compliant and recommends accepting or rejecting it, so that non-compliant batches stop before further processing.
  - Methods: logistic regression, random forest and SVM, with confidence thresholds and a cost matrix.
  - Results: at a 65% threshold the cost fell to 26% of the accept-all baseline. **Adding sensor-trajectory features did not improve accuracy.**
  - The exact decision point is not stated explicitly.
  - Relevance: a manufacturing "early termination" decision. It uses a predictive classifier plus cost thresholding (like early PresPM alarm work), not a learned policy. Its negative finding on sensor features is a useful counterpoint for the thesis.
  - Link: [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC10708579/)
- **LSTM fault-tolerant soft sensor for end-point and quality estimation. *Processes* 12:495 (2024). [S]**
  - Summary: two LSTMs combined so that end-point detection survives sensor failure.
  - Link: [MDPI PDF](https://mdpi-res.com/d_attachment/processes/processes-12-00495/article_deploy/processes-12-00495.pdf)
- **End-point detection patents [S]:**
  - Near-infrared spectroscopy plus SVM to detect the transition to steady state: [EP3399472](https://bvbvf1.bib-bvb.de/vufind/PrimoRecord/cdi_epo_espacenet_EP3399472C0/Details)
  - Feedback-corrected endpoint signal: [EP1410118](https://data.epo.org/gpi/EP1410118A1)
  - Older expert-system batch control: [US5058043](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/5058043)
  - Takeaway: industrial practice relies on thresholds and classifiers.
- **Kang et al. (2011). VM-embedded EWMA run-to-run control. *Expert Systems with Applications*. [S]**
  - Link: [Korea Univ.](https://pure.korea.ac.kr/en/publications/virtual-metrology-for-run-to-run-control-in-semiconductor-manufac/)
- **Wan & McLoone (2018). "Gaussian Process Regression for Virtual Metrology-enabled Run-to-Run Control in Semiconductor Manufacturing." *IEEE Trans. Semiconductor Manufacturing*. [S]**
  - Summary: the GPR variance tunes the EWMA controller.
  - Relevance: an uncertainty-aware prediction-to-action loop.
  - Link: [QUB accepted PDF](https://pureadmin.qub.ac.uk/ws/files/137825983/GPR_R2R_final_post_review_accepted_paper.pdf)
- **Weiss, Dhurandhar et al. (2013). Virtual metrology and run-to-run control with tensor models (KDD 2013). [S]**
  - Link: [IBM Research](https://research.ibm.com/publications/virtual-metrology-and-run-to-run-control-in-semiconductor-manufacturing)
- **Susto et al. (2012). Review of control and ML in semiconductor manufacturing, including VM and run-to-run control. [S]**
  - Link: [MURAL](https://mural.maynoothuniversity.ie/id/eprint/4184/)
- **RL for condition-based maintenance timing [S]:**
  - Knowles, Baglee, Wermter (2010), RL for maintenance scheduling: [PDF](https://www.informatik.uni-hamburg.de/wtm/ps/Knowles_SGAI2010_CR.pdf)
  - Erdem et al. (2025), "RL in CBM: A Survey" (INFUS): [record](https://gcris.ieu.edu.tr/entities/publication/36fe6a21-6af2-4643-b9f4-561b9cf9cf74)
  - Multi-asset deep RL for maintenance: [arXiv 2105.15119](https://arxiv.org/pdf/2105.15119)
  - Distributional RL (QR-DQN) for pump CBM: [arXiv 2602.00051](https://arxiv.org/pdf/2602.00051)
  - Takeaway: CBM timing is formulated as an MDP or optimal stopping problem over a degradation signal, structurally close to "when to stop spinning".

### Inferences
- Industry's "when to stop" is a **detect, predict, then threshold** pipeline. Learning a *stopping policy* from logged, confounded sensor trajectories, and evaluating it off-policy, is rare in this community. That is the gap PresPM-with-IoT can fill.
- CBM-RL is the closest formal analogue (optimal stopping on a continuous signal). It relies on simulated degradation models rather than event logs.

### Gaps
- I did not find a recent review of "batch end-point detection with ML".
- I did not find work that compares event-triggered and periodic decision-making for termination decisions in manufacturing. The *event-triggered control* literature in control theory may be relevant and was not searched.

---

## 5. Digital twins for decision and policy evaluation

### Takeaway
Digital twins are mainly used as **training and safety environments** for RL. I found no standard methodology for using a twin to *evaluate* a learned policy. One 2024 paper states that no standardised metric exists for whether a digital space is suitable for evaluation.

### Cited Findings
- **Cronrath et al. (2019).** Uses the digital twin as teacher and safety policy during RL for sheet-metal assembly fixtures. [S] [Chalmers](https://research.chalmers.se/en/publication/519202)
- **Digital twin for algorithm testing (2024), arXiv 2406.13145.** Proposes a "mean state error" metric and says no standardised metric exists for assessing a digital space for algorithm evaluation. Not manufacturing-specific. [S] [arXiv](https://www.arxiv.org/pdf/2406.13145)
- **Ali et al. (2025).** Digital twin plus SAC for real-time control in robotic additive manufacturing, with sim and physical validation. [S] [arXiv 2501.18016](https://arxiv.org/html/2501.18016v1)
- **Khdoudi et al. (2024).** Deep-RL digital twin for manufacturing process optimisation, injection moulding focus. *Systems* 12(2):38. [S] [MDPI](https://www.mdpi.com/2079-8954/12/2/38)
- **RL plus digital-twin optimisation, *Discover Internet of Things* (2024).** Notes limited adoption due to missing guidelines and "lack of evaluation in reality". [S] [PDF](https://oceanrep.geomar.de/61121/1/Discover_Internet_of_Things2024.pdf)
- **Comprehensive digital twin review Part 1 (2022), arXiv 2208.14197.** Notes that deep RL has only recently been applied to digital twins. [S] [arXiv](https://arxiv.org/pdf/2208.14197)

### Inferences
- The thesis' semi-synthetic simulator (ccgen/presbench), used as ground truth for policy evaluation, matches the digital-twin-as-evaluator idea. It can cite the missing evaluation standard as motivation.

### Gaps
- No manufacturing review specifically on simulation-based *off-policy evaluation* was found.

---

## 6. Process mining in manufacturing with sensor data (overlap with PresPM)

### Takeaway
Manufacturing process mining with IoT focuses on **event abstraction** (turning sensor streams into event logs) and on descriptive or diagnostic analysis (bottlenecks, root causes). I found no prescriptive or policy-learning work in this strand. The thesis' idea of keeping sensor-level decision points instead of abstracting to events goes in the opposite direction to this literature.

### Cited Findings
- **Brzychczy et al. (2024/2025).** Review of process mining on IoT sensor data in manufacturing. *Knowledge and Information Systems*. DOI 10.1007/s10115-024-02297-y. [V, record]
  - Summary: 36 papers. Event abstraction is the core challenge. Sensor data help with bottleneck identification and decision support.
  - Links: [Springer](https://link.springer.com/article/10.1007/s10115-024-02297-y); [OA PDF](https://epub.uni-bayreuth.de/8902/1/s10115-024-02297-y.pdf)
- **IoT Miner (2025), arXiv 2509.05769.** [S] [arXiv](https://arxiv.org/abs/2509.05769v1)
  - Summary: builds event logs from raw industrial sensor data in four stages: preprocessing, clustering, LLM labelling, log construction.
- **EL-SD, CEUR Vol-3298.** [S] [PDF](https://ceur-ws.org/Vol-3298/paper_DTE_625.pdf)
  - Summary: encodes sensor data into event logs for root-cause analysis, with industrial partner Farplas.
- **Bayomie et al. (2022). "Analyzing Manufacturing Process By Enabling Process Mining on Sensor Data."** [S] [WU Vienna](https://research.wu.ac.at/en/publications/analyzing-manufacturing-process-by-enabling-process-mining-on-sen/)
- **Process mining on production lines using IIoT (IEEE 2023, ITU).** [S] [ITU](https://research.itu.edu.tr/en/publications/application-of-process-mining-to-production-lines-using-industria/)
  - Summary: event-log construction with IoT ontologies, analysed in ProM.

### Inferences
- The manufacturing process-mining community is still at the "make a log from sensors" stage and has not moved to prescriptive use. PresPM on IoT-enriched logs, with decisions decoupled from events, seems to be unclaimed ground in this community (based on the papers found).

### Gaps
- I did not find any manufacturing PresPM paper. Confirming the absence needs the process-mining-side researcher's results.

---

## Overall judgement: does this community already do what the thesis proposes?

### Takeaway
**Partly, in pieces, but not together.**
- Process-control RL already acts at every sensor sample.
- Manufacturing causal ML (2024–2025) already does CATE- and DR-based policy learning, but for single, fixed-time decisions.
- End-point detection and CBM already address "when to stop", but by thresholding predictions or by MDPs on simulated models.

What I did **not** find:
- (a) learning start/stop *timing* policies from **observational, event-log-plus-sensor data** with counterfactual or off-policy evaluation;
- (b) an explicit study of **decision granularity** (event-aligned vs. every sensor reading vs. coarser) as a variable affecting learnability;
- (c) a semi-synthetic benchmark with known ground-truth timing effects for this setting. causalAssembly and CausalMan are benchmarks for *discovery*, not timing policies.

### Cited Findings (supporting the judgement)
- Process-control RL acts per control interval and uses NMPC as baseline — [Yoo et al. 2021 review](https://koasas.kaist.ac.kr/handle/10203/291729); [Yoo et al. 2021 CACE](https://dspace.kaist.ac.kr/bitstream/10203/280027/1/1-s2.0-S0098135420307912-main.pdf)
- Offline RL from historical batch data exists but has out-of-distribution action problems — [Wang et al. DYCOPS 2025](https://skoge.folk.ntnu.no/prost/proceedings/dycops-2025/DYCOPS2025_offline_program/contents/papers/0110.pdf); [Sobhani et al. 2024](https://www.aidic.it/escape34-pse24/programma/629Sobhani.docx)
- Causal ML in manufacturing concerns single decisions (rework; parameter setting) — [Schwarz et al. 2024](https://arxiv.org/abs/2406.11308); [INFORMS IJDS](https://pubsonline.informs.org/doi/10.1287/ijds.2024.0041)
- Causality in manufacturing is mostly discovery — [Vuković & Thalmann 2022](https://doaj.org/article/c82fc8b4147549c8b388b52c7657cc26)
- Early termination in batch production is done by classifier plus cost threshold, and sensor features did not help there — [Mählkvist et al. 2023](https://pmc.ncbi.nlm.nih.gov/articles/PMC10708579/)
- Manufacturing process mining with IoT is about event abstraction and diagnosis — [Brzychczy et al.](https://link.springer.com/article/10.1007/s10115-024-02297-y)

### Inferences
Suggested positioning: "Process-control RL decides at every sample but assumes a model or simulator and fixed timing. PresPM learns from logs but decides only at events. Manufacturing causal ML learns from observational data but for one fixed decision point. This thesis connects the three: off-policy and causal learning of *timing* decisions from IoT-enriched event logs, treating decision granularity as an experimental variable."
- Closest works to cite as nearest neighbours: Yoo et al. 2021 (phase segmentation), Kim et al. 2025 (quality plus energy-cost objective), Schwarz et al. 2024 (causal ML policy in manufacturing), Mählkvist et al. 2023 (early termination decision), and CBM-RL surveys (optimal stopping on a sensor signal).

### Gaps
- Not searched: event-triggered control (control theory), temporal abstraction and action-repeat / decision-frequency studies in RL, and dynamic treatment regimes / treatment-timing methods in biostatistics. These are the most likely places where "granularity versus learnability" has been studied, and should be checked before claiming novelty.
- Several entries are [S] (abstract or snippet only, or prior knowledge with a DOI). In particular, the IJDS 2025 author list and the Vater 2019 IEEE record need verification.
- I could not cover literature up to Oct 2026 exhaustively. The newest items found are from 2025 and early 2026 (arXiv 2602.00051, 2510.24272).
