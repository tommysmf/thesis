# Prescriptive Process Monitoring (PresPM): core literature, causal and RL methods, timing, benchmarking (status 2026-10-31)

Verification legend used throughout:
- **[V]** = verified in this session: the arXiv/DOI/publisher page was fetched, or a search result returned the primary page with matching title, authors and venue.
- **[V-meta]** = metadata verified (title, authors, venue, link), but the abstract or content came from search snippets or mirrors rather than the full text.
- **[S]** = secondhand: found only as a citation inside another paper (mostly the SCOPE reference list) or from prior knowledge. The link is a best-effort pointer and was not opened.

Session budget note: about 20 tool calls. The novelty-check searches (continuous-time, sensor-triggered, or time-based decision points in PresPM) were run in three phrasings. All three returned only event-aligned work (see Q6).

---

## Q1. Surveys and taxonomies of PresPM

### Takeaway
The main PresPM survey is still Kubrak et al. (PeerJ CS 2022, 37 papers). Its taxonomy covers objective, metrics, intervention type, modelling technique, data input and policy, and it calls for causal, real-world-validated methods. The alarm-based framing (Teinemaa et al. 2018; Fahrenkrog-Petersen et al. 2022) is the other conceptual cornerstone. I found no dedicated PresPM survey from 2024-2026 that synthesises the causal and RL work.

### Cited Findings
- **[V] Kubrak, Milani, Nolte, Dumas (2022). "Prescriptive process monitoring: Quo vadis?" PeerJ Computer Science 8:e1097. DOI 10.7717/peerj-cs.1097.**
  - Links: https://peerj.com/articles/cs-1097 ; arXiv https://arxiv.org/abs/2112.01769
  - Summary: SLR of 37 papers. Classifies methods by performance objective, metrics, intervention types, modelling techniques, data inputs and intervention policies. Calls for real-world validation, interventions beyond time and cost, and policies that account for causality and second-order effects.
  - Relevance: the standard taxonomy to position the thesis in. Its "data inputs" dimension, as reported here, is event-log based; sensor/IoT inputs are not listed as a category.
  - Source: [PeerJ](https://peerj.com/articles/cs-1097)
  - Conflict: one search snippet claimed a Kubrak et al. "Quo vadis" version in *Information Systems* 128 (2025). I could not confirm this, and it may be a confusion with another paper. Treat the PeerJ 2022 version as canonical. ([search snippet context](https://www.researchgate.net/publication/372342162_Prescriptive_Process_Monitoring_Under_Resource_Constraints_A_Reinforcement_Learning_Approach))
- **[V-meta] Fahrenkrog-Petersen, Tax, Teinemaa, Dumas, de Leoni, Maggi, Weidlich (2022). "Fire Now, Fire Later: Alarm-Based Systems for Prescriptive Process Monitoring." Knowledge and Information Systems 64(2):559-587. DOI 10.1007/s10115-021-01633-w.**
  - Links: arXiv https://arxiv.org/abs/1905.09568 ; OA copy https://edoc.hu-berlin.de/18452/27317
  - Summary: adds alarms on top of outcome predictions, with a parameterised cost model (intervention cost, mitigation effectiveness, cost of undesired outcome, compensation). Delaying alarms, i.e. letting the threshold change as the case progresses rather than firing at the first threshold crossing, lowers net cost on real logs.
  - Relevance: an early explicit treatment of "fire now vs. later" as a timing question. Alarm checks still happen only at event prefixes.
  - Source: [arXiv 1905.09568](https://arxiv.org/pdf/1905.09568)
- **[S] Teinemaa, Tax, de Leoni, Dumas, Maggi (2018). "Alarm-Based Prescriptive Process Monitoring." BPM Forum 2018, LNBIP 329.**
  - Link: arXiv https://arxiv.org/abs/1803.08706
  - Summary: the precursor of the above. Introduces the cost-model-driven alarm threshold optimisation over predictive outcome monitoring.
  - Relevance: same timing framing, evaluated per prefix length.
- **[V-meta] Huang et al. (2025). "A Survey on Causal Reinforcement Learning." IEEE TNNLS. DOI 10.1109/tnnls.2024.3403001.**
  - Link: https://doi.org/10.1109/tnnls.2024.3403001
  - Summary: a general causal RL taxonomy covering MDP, POMDP, bandits, imitation learning and dynamic treatment regimes. It is not PresPM-specific.
  - Relevance: background for positioning causal RL policies at arbitrary decision times.

### Inferences
- The surveys frame PresPM interventions around cases and prefixes. "Data inputs" means event attributes; sensor streams are not a category in the taxonomy as reported. This leaves room to position IoT-enriched PresPM as an unaddressed input type.

### Gaps
- I found no PresPM survey dated 2024-2026. If one exists, it was not indexed by my queries. The caller should check BPM/ICPM 2025-2026 proceedings directly.

---

## Q2. Causal PresPM (Bozorgi, Shoush and Dumas, KU Leuven group, de Leoni and others)

### Takeaway
Causal PresPM has gone from single binary treatments with CATE estimation (Bozorgi 2021/2023), to resource-constrained and uncertainty-aware triggering (Shoush and Dumas 2022), to combined causal and RL timing (Bozorgi 2023; Weytjens 2023/24). The KU Leuven line (De Moor, Weytjens, De Smedt, De Weerdt) has led on sequential interventions and evaluation (SimBank 2025, ProCause 2025, SCOPE 2025/26). Treatments are almost always binary or categorical. I found no continuous-dose treatment in PresPM.

### Cited Findings
- **[V-meta] Bozorgi, Teinemaa, Dumas, La Rosa, Polyvyanyy (2021). "Prescriptive Process Monitoring for Cost-Aware Cycle Time Reduction." ICPM 2021.**
  - Link: https://arxiv.org/abs/2105.07111
  - Summary: estimates the causal effect of a time-reducing intervention per ongoing case with orthogonal random forests. A user-defined policy then decides whether to trigger it.
  - Relevance: the canonical CATE-at-prefix approach; it is evaluated at event prefixes.
  - Source: [arXiv 2105.07111](https://arxiv.org/html/2105.07111)
- **[V-meta] Bozorgi, Teinemaa, Dumas, La Rosa, Polyvyanyy (2023). "Prescriptive process monitoring based on causal effect estimation." Information Systems.**
  - Link: https://findanexpert.unimelb.edu.au/scholarlywork/1763731-prescriptive-process-monitoring-based-on-causal-effect-estimation
  - Summary: journal extension of the 2021 paper to binary or real-valued outcomes, for example loan acceptance.
  - Source: [UniMelb record](https://findanexpert.unimelb.edu.au/scholarlywork/1763731-prescriptive-process-monitoring-based-on-causal-effect-estimation)
- **[V] Bozorgi, Dumas, La Rosa, Polyvyanyy, Shoush, Teinemaa (2023). "Learning When to Treat Business Processes: Prescriptive Process Monitoring with Causal Inference and Reinforcement Learning." CAiSE 2023, LNCS.**
  - Links: https://link.springer.com/chapter/10.1007/978-3-031-34560-9_22 ; arXiv https://arxiv.org/abs/2303.03572
  - Summary: combines causal effect estimation with RL to learn when to treat, maximising net gain. Conformal prediction separates cases that are likely positive, likely negative and uncertain, which speeds up learning. A treatment's effect changes over the case, so earlier treatment can be better. The agent reviews each case "after each event" and decides treat or not; RL beats empirical thresholding.
  - Relevance: **key precedent for "when to intervene"**. It defines the decision point explicitly as "after each event", which is exactly the event-aligned assumption the thesis challenges.
  - Sources: [arXiv 2303.03572](https://arxiv.org/abs/2303.03572); [CEUR summary of the decision point](https://ceur-ws.org/Vol-3407/paper6.pdf)
- **[V-meta] Shoush, Dumas (2022). "Prescriptive Process Monitoring Under Resource Constraints: A Causal Inference Approach." ICPM 2021 Workshops.**
  - Link: https://arxiv.org/abs/2109.02894
  - Summary: triggers interventions in ongoing cases to maximise a net-gain function when intervention resources are limited, using causal effect estimates.
  - Source: [arXiv 2109.02894](https://arxiv.org/html/2109.02894)
- **[V] Shoush, Dumas (2022). "When to Intervene? Prescriptive Process Monitoring Under Uncertainty and Resource Constraints." BPM Forum 2022, LNBIP.**
  - Links: https://link.springer.com/chapter/10.1007/978-3-031-16171-1_13 ; arXiv https://arxiv.org/abs/2206.07745
  - Summary: filters and ranks ongoing cases by prediction score, prediction uncertainty and causal effect, then triggers interventions to maximise gain given available resources. It explicitly addresses the trade-off between acting now under uncertainty and waiting for a later, more informed state.
  - Relevance: **directly about timing**. "Later" still means a later event or prefix, not an arbitrary time.
  - Source: [arXiv 2206.07745](https://arxiv.org/html/2206.07745v1)
- **[S] Shoush, Dumas (2022). "Intervening with Confidence: Conformal Prescriptive Monitoring of Business Processes."**
  - Link: DBLP author page https://dblp.org/search?q=Intervening+with+Confidence+Shoush
  - Summary: uses conformal prediction to quantify uncertainty before triggering interventions. Cited in SCOPE.
  - Source: [SCOPE references](https://arxiv.org/html/2512.17629)
- **[V-meta] Shoush, Dumas (2023 arXiv; 2025 per SCOPE reference). "Prescriptive Process Monitoring Under Resource Constraints: A Reinforcement Learning Approach."**
  - Link: https://arxiv.org/abs/2307.06564
  - Summary: an RL agent decides which cases to intervene on and when, under limited resources. Conformal prediction makes the agent uncertainty-aware. On real logs it reaches higher net intervention gain.
  - Relevance: an RL timing baseline. Its state is the per-event prefix.
  - Source: [arXiv 2307.06564](https://arxiv.org/abs/2307.06564)
- **[S] Shoush, Dumas (2025). "White box specification of intervention policies for prescriptive process monitoring."**
  - Link: DBLP https://dblp.org/search?q=White+box+specification+of+intervention+policies
  - Summary: interpretable, user-specifiable intervention policies. Cited in SCOPE; content not checked.
  - Source: [SCOPE references](https://arxiv.org/html/2512.17629)
- **[S] de Leoni, Dees, Reulink (2020). "Design and evaluation of a process-aware recommender system based on prescriptive analytics." ICPM 2020.**
  - Link: DBLP https://dblp.org/search?q=process-aware+recommender+system+prescriptive+analytics+de+Leoni
  - Summary: recommends interventions per case from predictive models. SCOPE adapts it as the "SEP-S" baseline: a separate S-learner per decision point, with no alignment between decisions.
  - Source: [SCOPE](https://arxiv.org/html/2512.17629)
- **[S] Padella, de Leoni, Dogan, Galanti (2022). "Explainable Process Prescriptive Analytics." ICPM 2022.**
  - Link: DBLP https://dblp.org/search?q=Explainable+Process+Prescriptive+Analytics
  - Summary: explainable next-activity recommendations (from prior knowledge, not verified this session).

### Inferences
- In every causal PresPM method I found, treatment is binary (treat or not) or a small categorical set. The SimBank interest rate, for example, has three levels ([SCOPE](https://arxiv.org/html/2512.17629)). Continuous treatments, such as intervention intensity or a continuous delay, are an open gap.
- All of these methods compute features over event prefixes. The decision "now" is evaluated only when a new event arrives.

### Gaps
- I did not find a Bozorgi paper dated 2024-2026 on "resource-aware" or "conformal causal" PresPM beyond the 2023 work. It may exist under Bozorgi's PhD thesis (UniMelb), which I did not check.

---

## Q3. RL-based PresPM, next-best-action, and offline RL from event logs

### Takeaway
RL in PresPM splits into two lines. One is online RL on simulators or synthetic environments (Metzger; Weytjens; Shoush). The other learns MDPs or offline RL directly from logs (Branchi KMeans-MDP; CQL comparison; FORLAPS; SCOPE's causal backward induction). In all of them the MDP step is an event or activity, never wall-clock time.

### Cited Findings
- **[V-meta] Weinzierl, Dunzer, Zilker, Matzner (2020). "Prescriptive Business Process Monitoring for Recommending Next Best Actions." BPM Forum 2020.**
  - Link: https://arxiv.org/abs/2008.08693
  - Summary: turns the most likely next activities (from a DL predictor) into KPI-optimal next best actions. Uses process simulation to keep recommendations control-flow conformant.
  - Relevance: NBA framing, where the decision happens at each next event.
  - Source: [arXiv 2008.08693](https://arxiv.org/pdf/2008.08693)
- **[V-meta] Branchi, Di Francescomarino, Ghidini, Massimo, Ricci, Ronzani (2022). "Learning to act: a Reinforcement Learning approach to recommend the best next activities." BPM Forum 2022.**
  - Link: https://arxiv.org/abs/2203.15398
  - Summary: builds an MDP from past executions and learns the optimal policy with RL, from the viewpoint of an actor facing an uncontrollable environment. Evaluated on two real-life scenarios.
  - Source: [arXiv 2203.15398](https://arxiv.org/pdf/2203.15398)
- **[S] Branchi et al. (2023). "Recommending the optimal policy by learning to act from temporal data."**
  - Link: DBLP https://dblp.org/search?q=Recommending+the+optimal+policy+by+learning+to+act+from+temporal+data
  - Summary: extension of the above that clusters prefix states with KMeans and runs Q-learning. SCOPE uses it as the "KMeans-Q" baseline.
  - Source: [SCOPE](https://arxiv.org/html/2512.17629)
- **[V-meta] "Learning optimal policies from event logs through reinforcement learning: a comparison of deep and MDP-based approaches." arXiv 2303.09209; Information Systems (2026), S0306437926000773.**
  - Links: https://arxiv.org/abs/2303.09209 ; https://www.sciencedirect.com/science/article/pii/S0306437926000773
  - Summary: adapts Conservative Q-Learning (offline deep RL) with an LSTM encoder to process mining and compares it with MDP-based approaches on a synthetic process model.
  - Relevance: the offline-RL-from-logs baseline. Authors not verified; probably the Branchi/FBK group.
  - Source: [ScienceDirect](https://www.sciencedirect.com/science/article/pii/S0306437926000773)
- **[V-meta] Abbasi et al. (2025). "FORLAPS: An Innovative Data-Driven Reinforcement Learning Approach for Prescriptive Process Monitoring" (later titled "An innovative data-driven and adaptive RL approach for context-aware PresPM").**
  - Link: https://arxiv.org/abs/2501.10543
  - Summary: offline RL with state-dependent reward shaping and process-aware data augmentation to recommend the next best activity. Evaluated on logs from a Canadian energy regulator. Assumes no unobserved confounding.
  - Source: [arXiv 2501.10543](https://arxiv.org/html/2501.10543v2)
- **[S] Kotsias et al. Batch RL (Fitted Q-Iteration / Neural FQI) for resource allocation from event logs.**
  - Summary: mentioned in a search summary only; no link verified.
  - Source: [search context via FORLAPS page](https://www.researchgate.net/publication/388232359_FORLAPS_An_Innovative_Data-Driven_Reinforcement_Learning_Approach_for_Prescriptive_Process_Monitoring)
- **[V-meta] "Reinforcement Learning-supported AB Testing of Business Process Improvements" (Satyal/Weber line).**
  - Links: https://arxiv.org/abs/2303.10756 ; journal version SoSyM https://link.springer.com/article/10.1007/s10270-024-01229-2
  - Summary: uses RL (bandits) to route cases between process variants during AB tests.
  - Relevance: peripheral; this is process-level rather than case-intervention-level.

### Inferences
- Every RL formulation discretises time by events or activities. RL on IoT logs would need a semi-MDP or continuous-time formulation (decisions at sensor ticks, with variable inter-decision times). That is new for PresPM.

### Gaps
- I found no PresPM paper that uses a semi-MDP or options framework, or continuous-time RL.

---

## Q4. The three thesis-description references

### Takeaway
Two of the references are the KU Leuven sequential-PresPM and benchmarking papers (SCOPE, SimBank). The third (Springer s44311-025-00011-x) is **Bertrand et al. 2025, "Approaches for IoT-enhanced predictive process monitoring"** in *Process Science*. It covers IoT-enriched *predictive*, not prescriptive, monitoring.

### Cited Findings
- **[V] De Moor, Weytjens, De Smedt, De Weerdt. "SCOPE: Sequential Causal Optimization of Process Interventions." arXiv 2512.17629 (v1 19 Dec 2025, v4 9 Jun 2026).** No peer-reviewed venue is listed on arXiv.
  - Link: https://arxiv.org/abs/2512.17629
  - Method: learns aligned sequential interventions by **backward induction** over decision points, with causal learners trained on observational data (a dynamic-treatment-regime style approach). No simulator or RL process approximation is needed, which avoids the reality gap.
  - **Decision points**: defined as "a prespecified or discovered point in the process where an intervention may occur". A case visits only some of them; the history is the event prefix before the decision point. There is no time-based definition.
  - Data: SimBank (2 sequential decisions: procedure choice and a 3-level interest rate; profit KPI) and the new semi-synthetic **SimBPIC17** from BPIC17_W (call-or-wait on incomplete files; 2-6 decision points; cost KPI).
  - Baselines: KMeans-Q (Branchi), SEP-S (de Leoni, adapted), random policy, and an exhaustive upper bound. It outperforms these on the KPI.
  - Limitations stated: SUTVA, sequential ignorability, training cost, error accumulation. **The paper does not discuss intervention timing, continuous treatments, or decision points not aligned with events.**
  - Relevance: the closest methodological ancestor. The thesis can be framed as relaxing SCOPE's "prespecified or discovered decision points" to arbitrary sensor-time decision points.
  - Sources: [arXiv abs](https://arxiv.org/abs/2512.17629); [HTML](https://arxiv.org/html/2512.17629)
  - Minor conflict: one search summary described SCOPE as "KMeans + offline Q-learning". That describes the KMeans-Q baseline, not SCOPE. The full text confirms backward induction with causal learners.
- **[V] De Moor, Weytjens, De Smedt, De Weerdt. "SimBank: from Simulation to Solution in Prescriptive Process Monitoring." arXiv 2506.14772 (v1 28 Mar 2025, v3 2 Jul 2025).** SCOPE cites it as De Moor et al. 2026; the venue was not confirmed.
  - Link: https://arxiv.org/abs/2506.14772
  - Summary: a loan-application simulator with parallelism and loops, calibrated on common logs. It supports online and offline PresPM, controllable confounding, and **ground-truth outcomes under every intervention for each test case**. Includes a proof-of-concept benchmark.
  - Relevance: the template for how to build a simulator for IoT-PresPM evaluation, where the true outcome under any intervention at any time is needed.
  - Source: [arXiv 2506.14772](https://arxiv.org/abs/2506.14772)
- **[V-meta] Bertrand, Stevens, Deforce, De Smedt, De Weerdt, Serral (2025). "Approaches for IoT-enhanced predictive process monitoring." Process Science 2(1), Article 7. DOI 10.1007/s44311-025-00011-x.** Published online 1 May 2025.
  - Link: https://link.springer.com/article/10.1007/s44311-025-00011-x
  - Summary: the Springer page redirected to a login and Crossref returned metadata without the abstract. From the title and context, it compares ways to incorporate IoT sensor data into predictive process monitoring.
  - Relevance: directly informs how sensor streams are encoded for the predictive and causal models inside a PresPM policy. Note that it is predictive, not prescriptive.
  - Source: [Crossref metadata](https://api.crossref.org/works/10.1007/s44311-025-00011-x)
- **[V-meta] Related IoT event-log infrastructure (Bertrand and Serral):**
  - NICE IoT-centric event log format, ICPM 2023: https://iris.uniroma1.it/handle/11573/1691514
  - CORE metamodel on OCEL 2.0: https://arxiv.org/html/2506.21300v2
  - DataStream XES extension (Future Internet 2023): https://ideas.repec.org/a/gam/jftint/v15y2023i3p109-d1096628.html
  - Sensor-to-event correlation and process-awareness classification: https://arxiv.org/abs/2405.08528
  - One of these papers notes that sensor data is noisy and voluminous and is collected independently of the process, so integrating it with events is a major obstacle. Source: [arXiv 2506.21300](https://arxiv.org/html/2506.21300v3)

### Gaps
- I could not read the Bertrand et al. 2025 abstract and findings (paywall redirect). The caller should get them via KU Leuven access.

---

## Q5. Intervention timing and the earliness-accuracy trade-off

### Takeaway
Timing is a recognised PresPM problem with roughly four strands:
1. Alarm thresholds that may vary with case progress (Teinemaa 2018; Fahrenkrog-Petersen 2022).
2. Reliability-thresholded triggering of proactive adaptation, learned by online RL (Metzger et al. 2019-2023).
3. Causal and RL "when to treat" (Bozorgi 2023; Shoush and Dumas 2022, 2023).
4. Timed single interventions, comparing causal inference with RL (Weytjens et al. 2023/24).

All of them measure "time" as prefix length or event index.

### Cited Findings
- **[V-meta] Metzger, Kley, Palm (2020). "Triggering Proactive Business Process Adaptations via Online Reinforcement Learning." BPM 2020.**
  - Link: https://sse.uni-due.de/aktuelles/alle-news-insights/artikel/anpassung-von-geschaeftsprozessen-durch-online-reinforcement-learning
  - Summary: learns the prediction-reliability threshold for triggering adaptations at run time, because fixed thresholds are suboptimal under non-stationarity. Reported (summary page only) about 8% lower execution cost than empirical thresholding on 3 public datasets.
  - Source: [UDE news page](https://sse.uni-due.de/aktuelles/alle-news-insights/artikel/anpassung-von-geschaeftsprozessen-durch-online-reinforcement-learning)
- **[V-meta] Metzger, Kley, Rothweiler, Pohl (2023). "Automatically reconciling the trade-off between prediction accuracy and earliness in prescriptive business process monitoring." Information Systems.**
  - Links: arXiv https://arxiv.org/abs/2307.05939 ; DBLP https://dblp.l3s.de/d2r/resource/publications/journals/is/MetzgerKRP23
  - Summary: earlier predictions give more time to adapt but are less accurate. Compares existing approaches to this trade-off on 4 public logs with 2 types of prediction model, measuring cost savings.
  - Source: [arXiv 2307.05939](https://arxiv.org/abs/2307.05939v1)
- **[V-meta] Metzger, Neubauer, Bohn, Pohl (2019). "Proactive Process Adaptation Using Deep Learning Ensembles." CAiSE 2019.**
  - Link: slides https://es.slideshare.net/andreasmmetzger/proactive-process-adaptation-using-deep-learning-ensembles
  - Summary: ensemble-based reliability estimates; about 27% average cost savings versus a static prediction point.
  - Source: [search summary](https://dblp.l3s.de/d2r/resource/publications/journals/is/MetzgerKRP23)
- **[V-meta] Weytjens, Verbeke, De Weerdt (2023/2024). "Timing Process Interventions with Causal Inference and Reinforcement Learning" (arXiv); BPM version "Timed Process Interventions: Causal Inference vs. Reinforcement Learning."**
  - Links: https://arxiv.org/abs/2306.04299 ; code https://github.com/VerbekeLab/TimedProcessInterventions
  - Summary: a single intervention that can be placed at any point in the case (one shot). Synthetic data enables genuine online RL and a ground-truth comparison. RL policies beat causal inference and approach perfect policies, while causal inference remains useful when online learning is impossible.
  - Relevance: **the closest prior work on "timing"**. "Any point" still means any event of the case, since the state space is event-based.
  - Source: [arXiv 2306.04299](https://arxiv.org/abs/2306.04299)
- **[S] Teinemaa, Dumas, Leontjeva, Maggi (2018). "Temporal stability in predictive process monitoring." Data Mining and Knowledge Discovery 32.**
  - Link: arXiv https://arxiv.org/abs/1712.04165
  - Summary: measures how stable successive predictions are over prefixes. Relevant to how often to re-decide when decision points are dense (sensor-level).

### Inferences
- Moving from events to sensor readings makes decision points far denser. This is the earliness-accuracy trade-off taken to its limit: more chances to intervene early, but noisier states and more temporally correlated decisions. Temporal stability and threshold-learning results (Teinemaa 2018; Metzger 2020) are therefore directly relevant to the granularity-versus-learnability question.

### Gaps
- No paper studies how decision-point **granularity** itself (events vs. fixed time steps vs. sensor ticks) affects policy value or learnability. I found nothing on this.

---

## Q6. Decision points not at events (novelty check)

### Takeaway
**I found no PresPM paper that defines decision points by time, continuous time, or sensor triggers.** Every method found is event-aligned:
- "After each event" (Bozorgi 2023)
- Prefix or next-activity based (Weinzierl, Branchi, FORLAPS)
- "Prespecified or discovered points in the process" (SCOPE)

The IoT process-mining work (Bertrand, Serral et al.) is predictive or descriptive, not prescriptive. The thesis RQ looks novel, subject to the gaps below.

### Cited Findings
- Bozorgi et al. define the decision point as after each event — [CEUR summary](https://ceur-ws.org/Vol-3407/paper6.pdf); [arXiv 2303.03572](https://arxiv.org/abs/2303.03572)
- SCOPE defines decision points as prespecified or discovered process points, with the history taken as the event prefix — [arXiv HTML](https://arxiv.org/html/2512.17629)
- Weytjens et al. timed interventions use a one-shot intervention at some point in the process, with an event-based state space — [arXiv 2306.04299](https://arxiv.org/abs/2306.04299)
- A search for continuous-time or sensor PresPM returned only generic IoT predictive-maintenance material. Examples are an AIoT prescriptive maintenance review ([PMC12737171](https://pmc.ncbi.nlm.nih.gov/articles/PMC12737171/)) and process mining on distributed sensor sources, which notes that sensor data breaks the one-event-one-activity assumption ([arXiv 2506.02830](https://arxiv.org/pdf/2506.02830)).
- The IoT event-log work treats sensor data as something to integrate into event logs, not as a basis for decision points — [arXiv 2506.21300](https://arxiv.org/html/2506.21300v3)

### Inferences
- The likely closest neighbours outside PresPM are prescriptive maintenance (condition-based maintenance, with decisions at sensor readings), dynamic treatment regimes with irregular visit times, and continuous-time or semi-MDP RL. A related-work chapter should bridge to these.

### Gaps
- My searches were Google/Bing-style web search only, not full Google Scholar or DBLP proceedings sweeps. Lower-visibility workshop papers (for example ICPM workshops, ML4PM, or the PresPM doctoral consortium) on time-based decision points could have been missed. This is especially true for work by Bertrand, Serral, Stevens or De Smedt on IoT-*prescriptive* monitoring in 2025-2026.
- I did not check whether Metzger's reliability-triggered adaptation was ever applied with continuous sensor data, for example in his self-adaptive systems exemplars.

---

## Q7. Benchmarking and evaluation methodology for PresPM

### Takeaway
Evaluation is the field's acknowledged weak point, because historical logs lack counterfactual outcomes. The KU Leuven group answers this with simulators that have full ground truth (SimBank), with generative counterfactual-outcome models fitted to real logs (ProCause, which extends RealCause with temporal backbones), and with semi-synthetic benchmarks (SimBPIC17). Online RL in particular needs simulators (Weytjens et al.).

### Cited Findings
- **[V] SimBank**: ground-truth outcomes under every intervention, plus confounding robustness tests — [arXiv 2506.14772](https://arxiv.org/abs/2506.14772)
- **[V-meta] De Moor, Weytjens, De Smedt (+ possibly De Weerdt) (2025). "ProCause: Generating Counterfactual Outcomes to Evaluate Prescriptive Process Monitoring Methods." ICPM 2025 (per search summary).**
  - Link: https://arxiv.org/abs/2509.00797
  - Summary: extends RealCause, which was designed for static interventions and ignores temporal dependencies with a single TARNet architecture. ProCause adds S- and T-learners, an ensemble and LSTM backbones, and is validated on a simulator with known ground truth. It also contrasts absolute and relative evaluation performance.
  - Relevance: an evaluation path for IoT logs that have no ground truth.
  - Source: [arXiv 2509.00797](https://arxiv.org/pdf/2509.00797)
- **[S] Neal, Huang, Raghupathi (2020). "RealCause: Realistic Causal Inference Benchmarking."**
  - Link: https://arxiv.org/abs/2011.15007
  - Summary: the generative benchmark ProCause builds on.
- **[V] SimBPIC17**, SCOPE's semi-synthetic sequential benchmark built from BPIC17, is released as reusable — [arXiv 2512.17629](https://arxiv.org/abs/2512.17629)
- Weytjens et al. argue that most PresPM experiments on historical data compromise evaluation accuracy and rule out online RL, which motivates synthetic data — [arXiv 2306.04299](https://arxiv.org/abs/2306.04299)
- SCOPE notes that real logs do not allow direct ground-truth evaluation of learned policies — [arXiv 2512.17629](https://arxiv.org/pdf/2512.17629)

### Inferences
- No existing benchmark (SimBank, SimBPIC17, ProCause outputs) contains sensor streams or allows interventions between events. An IoT-PresPM thesis would likely need its own simulator, for example a SimBank-like design with sensor-state dynamics where the intervention time is a free variable. This is a contribution in its own right.
- Off-policy evaluation estimators (IPS, doubly robust, FQE) were not explicitly found in PresPM papers in this session. Evaluation relies on simulators or generative counterfactuals instead.

### Gaps
- I did not verify whether any PresPM paper uses formal OPE estimators such as doubly robust or FQE. This needs a targeted search.

---

## Summary assessment: what PresPM has and has not done (for the RQ)

| Topic | Status in PresPM literature | Key refs |
|---|---|---|
| When to intervene / timing | **Done, but event-indexed**: alarm thresholds, reliability-triggered RL, causal + RL "when to treat", one-shot timed interventions | [Fahrenkrog-Petersen](https://arxiv.org/abs/1905.09568), [Metzger 2023](https://arxiv.org/abs/2307.05939), [Bozorgi 2023](https://arxiv.org/abs/2303.03572), [Shoush 2022](https://arxiv.org/abs/2206.07745), [Weytjens](https://arxiv.org/abs/2306.04299) |
| Decision point definition | Always events, prefixes or process points (prespecified or discovered). **Not found: time-based, continuous, or sensor-triggered** | [SCOPE](https://arxiv.org/html/2512.17629) |
| Multiple / sequential interventions | Emerging: NBA (Weinzierl), MDP/RL (Branchi, FORLAPS, CQL), causal backward induction (SCOPE) | [SCOPE](https://arxiv.org/abs/2512.17629), [FORLAPS](https://arxiv.org/abs/2501.10543) |
| Continuous treatments | **Not found**: treatments are binary or small categorical sets | [SCOPE](https://arxiv.org/html/2512.17629) |
| Sensor / IoT data | Only in predictive and descriptive PM (Bertrand et al. 2025; NICE; CORE). **Not found in prescriptive PM** | [Bertrand 2025](https://link.springer.com/article/10.1007/s44311-025-00011-x) |
| Benchmarking | SimBank, ProCause, SimBPIC17; no IoT benchmark | [SimBank](https://arxiv.org/abs/2506.14772), [ProCause](https://arxiv.org/abs/2509.00797) |
