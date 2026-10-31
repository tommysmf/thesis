# IoT-Enriched Process Mining: Literature, Datasets, Recognised Challenges, and Prescriptive Gaps

Scope: IoT/sensor data combined with event logs, event abstraction, IoT log formats (XES SensorStream/DataStream, NICE, CORE/OCEL), predictive monitoring that uses IoT context, and a novelty check for prescriptive monitoring with sensor-level decision points. Search date: 2026-10-31.

**Verification legend:** **[V]** = I fetched the primary page (arXiv abstract page or Zenodo record) and checked the metadata. **[S]** = secondhand: the metadata comes from search-engine snippets, an aggregator (bibbase, dblp, ResearchGate), or background knowledge and was not checked on the primary page. Treat [S] author lists and venues as needing a check before citing.

Method note: Springer pages (link.springer.com) redirected to a login wall, the Zenodo community listing page and the Zenodo API both failed to return records, and the CEUR PDF of the IoPT repository paper could not be parsed. The findings below reflect those limits. Budget was about 25 tool calls, so this list is wide but **not exhaustive**. The Gaps sections name the obvious next searches.

---

## 1. Manifestos, agendas and challenge papers for IoT + BPM/process mining

### Takeaway
There is a small, tightly connected community: TUM (Mangler, Rinderle-Ma, Ehrendorfer), Trier/DFKI (Grüger, Malburg, Bergmann), KU Leuven (Bertrand, Serral), St. Gallen (Seiger, Franceschetti, Weber), Rome (Leotta, Mecella), and Koschmider (Bayreuth). It has produced a manifesto (2020), a challenge-and-framework paper (2024), and a review of sensor-based process mining (2025). All of them frame the core problem as **granularity mismatch and event abstraction**, that is, turning continuous low-level sensor data into discrete process events. None of them frames it as **decision-making between events**.

### Cited Findings (annotated list)

1. **The Internet of Things Meets Business Process Management: A Manifesto.** Janiesch, C. et al. (23 authors). 2020. *IEEE Systems, Man, and Cybernetics Magazine* 6(4):34–44, DOI 10.1109/MSMC.2020.3003135. Preprint: arXiv:1709.03628 (2017). [S] — [arXiv PDF](https://arxiv.org/pdf/1709.03628); [TU/e page](https://pa.win.tue.nl/the-internet-of-things-meets-business-process-management-a-manifesto/)
   - *Summary:* The manifesto argues that BPM concepts can help manage IoT applications and that the IoT, in turn, requires BPM to be extended. It lists challenges at the BPM–IoT intersection; the 2024 framework paper (item 2) refers to 16 of them.
   - *Relevance:* This is the founding agenda reference for the thesis introduction. The individual challenges were not extracted here, so read the PDF for the ones on data and granularity.

2. **From Internet of Things Data to Business Processes: Challenges and a Framework.** Mangler, J., Seiger, R., Benzin, J.-V., Grüger, J., Kirikkayis, Y., Gallik, F., Malburg, L., Ehrendorfer, M., Bertrand, Y., Franceschetti, M., Weber, B., Rinderle-Ma, S., Bergmann, R., Serral Asensio, E., Reichert, M. arXiv:2405.08528, v1 14 May 2024, v2 22 May 2024. No journal reference is listed. [V] — [arXiv](https://arxiv.org/abs/2405.08528)
   - *Summary:* IoT sensor data is "typically at a lower granularity" than process events. The paper asks three questions: which sensor values group into a process event, which mark its start and end, and which are related but non-essential. It proposes a semi-automatic framework with plug-in steps for event extraction, abstraction and correlation, and instantiates it in a smart-manufacturing demonstration. It also defines a spectrum of process awareness, from none to full, where full means every sensor–process relation is known ([arXiv HTML v2](https://arxiv.org/html/2405.08528v2)).
   - *Relevance:* This is the closest statement of the granularity problem. It treats sensor data only as something to **abstract into events**, never as possible decision moments. That is direct evidence for the gap the thesis targets.

3. **Process mining on sensor data: a review of related works.** Brzychczy, E., Aleknonytė-Resch, M., Janssen, D., Koschmider, A. 2025. *Knowledge and Information Systems* 67:4915–4948, DOI 10.1007/s10115-024-02297-y. [S] — [Springer](https://link.springer.com/article/10.1007/s10115-024-02297-y)
   - *Summary:* The review screens 36 papers. It asks which sensor types are common or under-represented, which process mining tasks have been applied to sensor data, and what best practices exist. It names abstraction of raw sensor data into discrete events as the core challenge.
   - *Relevance:* This is the most recent systematic review. Check whether any of the 36 papers covers predictive or prescriptive tasks; per the snippets, the emphasis is discovery and abstraction.

4. **Internet of Processes and Things: A Repository for IoT-Enriched Event Logs in Smart Environments.** Ehrendorfer, M., Bertrand, Y., Malburg, L., Mangler, J., Grüger, J., Rinderle-Ma, S., Bergmann, R., Serral Asensio, E. 2023. BPM 2023 Demonstration & Resources Forum, CEUR-WS vol. 3469, pp. 92–96. [S] (metadata from bibbase; the PDF could not be parsed) — [CEUR PDF](https://ceur-ws.org/Vol-3469/paper-16.pdf); [bibbase](https://bibbase.org/network/publication/ehrendorfer-bertrand-malburg-mangler-grger-rinderlema-bergmann-asensio-internetofprocessesandthingsarepositoryforiotenrichedeventlogsinsmartenvironments-2023)
   - *Summary:* The paper notes that research on object-centric process mining, **predictive process monitoring** and IoT-based process enhancement lacks real-world open datasets. It presents the Zenodo IoPT community as a place to collect well-documented IoT-enhanced logs.
   - *Relevance:* This is the citation for the thesis datasets. It explicitly lists predictive monitoring as a target use, but **not prescriptive** monitoring.

5. **An Expert-Validated Bridging Model for IoT Process Mining.** Bertrand, Y. et al. (exact authors not verified). Around 2023/2024. [S] — [ResearchGate](https://www.researchgate.net/publication/378073685_An_Expert-Validated_Bridging_Model_for_IoT_Process_Mining)
   - *Summary:* The paper derives 10 requirements for an IoT-enhanced event log model from four main challenges. It finds that both XES and OCEL have important limitations for storing IoT-enhanced logs.
   - *Relevance:* This is background for the requirements behind log formats. It is secondhand only.

### Inferences
- Across these agenda papers, the IoT-specific challenges are: (a) granularity mismatch, (b) continuous, distributed and ambiguous data versus discrete events, (c) event abstraction and correlation to cases, (d) data quality (delayed, lost or duplicated readings, clock drift), (e) inadequate log formats (XES/OCEL), and (f) the scarcity of real datasets. "Decision points between events" does **not** appear as a named challenge in any source I found.

### Gaps
- I did not extract the full list of 16 manifesto challenges; the PDF was not fetched.
- The Bertrand, Van den Abbeele, Gatti, De Weerdt work named in the brief was not found under those names. The KU Leuven IoT process mining line runs mainly through Bertrand and Serral (NICE, the bridging model, CORE).

---

## 2. The Zenodo IoPT community and its datasets

### Takeaway
The Zenodo community "Internet of Processes And Things" (IoPT, https://zenodo.org/communities/iopt) collects IoT-enhanced event logs. Most of them use the XES SensorStream/DataStream format. Confirmed or likely records include: the cotton candy log (TUM, 2025), the Trier smart factory log and its injected-data-quality-issues follow-up, a port cargo OCEL, and activity-detection evaluation datasets from St. Gallen. I could not enumerate the community programmatically.

### Cited Findings
- **The community** is named "Internet of Processes And Things" and has Records, Members, Curation policy and About pages. The record listing did not render through the fetch tool. — [Zenodo community](https://zenodo.org/communities/iopt) [V, name only]

- **Cotton Candy XES YAML (Power Consumption, Environment, Temperatures, Metrology).** Arteaga Garcia, N. (data collector, TUM), Mangler, J. (contact, TUM and University of Vienna). Published 29 Sept 2025, v1, DOI 10.5281/zenodo.17226615, CC BY 4.0, in the IoPT community. [V] — [Zenodo](https://zenodo.org/records/17226615)
  - Recorded with the cpee.org process engine by TUM's i17 chair. It contains raw, refined and aggregated data in the "XES SensorStream format".
  - Hardware: a UR5e robot, a Royal Catering RCZK-1030-W cotton candy machine, environment temperature and humidity sensors, an internal machine temperature sensor, and an RS232 precision scale. The robot touch-checks the candy size and weighs each batch. **A human presses a button to mark when forming starts and ends.** Process models are embedded as special events.
  - **The stated purpose is a digital twin for optimising the machine's heating and spinning actuation, to improve quality and throughput.** This is effectively a control and prescriptive motivation, which supports the thesis framing: interventions on heating and spinning can happen at any sensor reading.
  - It cites arXiv:2206.11392 (SensorStream) as the format reference. File: cotton-candy.zip, 19.7 MB.

- **An IoT-Enriched Event Log for Process Mining in Smart Factories** (the Trier/DFKI Fischertechnik smart factory). Malburg, L., Grüger, J., Bergmann, R. arXiv:2209.02702, submitted 6 Sept 2022. [V] — [arXiv](https://arxiv.org/abs/2209.02702). Dataset: [Zenodo 7795547](https://zenodo.org/records/7795547) (marked deprecated; the current version is on [figshare](https://figshare.com/articles/dataset/Dataset_An_IoT-Enriched_Event_Log_for_Process_Mining_in_Smart_Factories/20130794)) [S]
  - *Summary:* The paper addresses the shortage of IoT-based logs and notes that most existing ones are synthetic. It presents an XES log recorded from a physical smart factory, introduces the SensorStream XES extension, and gives a preliminary analysis. According to snippets, the log deliberately includes data-quality issues: delayed, lost or duplicated events and time-server drift ([arXiv PDF](https://arxiv.org/pdf/2209.02702)).
  - *Relevance:* This is likely the "Trier smart factory" dataset the thesis uses. Cite it for the data-quality challenge.

- **An IoT-Enriched Event Log for Smart Factories with Injected Data Quality Issues.** Zenodo 15487019, DOI 10.5281/zenodo.15487019. It builds on the dataset above, follows the DataStream XES extension, and ships as DQI Event Log.zip (82.8 MB). [S] — [Zenodo](https://zenodo.org/records/15487019)

- **IoT-Enriched OCEL Dataset for the Cargo Pickup Process at a Major Chinese Port.** Zenodo 22019684. An object-centric log enriched with IoT data. [S] — [Zenodo](https://zenodo.org/records/22019684)

- **Activity detection datasets (St. Gallen, Seiger group):** "CEP-based Activity Detection Services generated from IoT Data" ([Zenodo 8087219](https://zenodo.org/records/8087219)); "Prototype of an IoT-based Activity Detection Service Generator with Evaluation Datasets" ([Zenodo 15436046](https://zenodo.org/records/15436046)); "Dataset used for Evaluation of Radiant" ([Zenodo 15068153](https://zenodo.org/records/15068153)). [S]

- **Data set from Fischertechnik Smart Factory Model at University of St. Gallen.** [Zenodo 7440490](https://zenodo.org/record/7440490). [S]

- **Reproducibility package for "From Sensor Signals to Event Logs: Challenges of Process Mining in Cyber Physical Production Systems"** (ICPS 2026, TU Wien, author listed as Just, V. P.). It covers preprocessing of IIoT runtime data, event log generation and discovery. [S] — [Zenodo 18673199](https://zenodo.org/records/18673199)

### Inferences
- The cotton candy dataset is the most natural testbed for the RQ. It has continuous actuation-relevant signals (temperatures, power) between discrete events, a quality outcome (weight and size), and an explicit optimisation goal stated by its creators.

### Gaps
- **I did not find the Vienna tram dataset or its associated paper.** Search the community page directly or Zenodo for "tram" or "Wiener Linien".
- I did not find a dedicated publication describing the cotton candy dataset. The record cites only the SensorStream paper. The thesis repo's submodule "ProClause" may relate to this group; it was not checked.
- There is no full enumeration of IoPT records, because the Zenodo listing and API failed. Fetch https://zenodo.org/communities/iopt/records manually in a browser.

---

## 3. IoT event log formats: SensorStream/DataStream XES, NICE, CORE (OCEL-based)

### Takeaway
The format line ran from SensorStream XES (2022) to DataStream XES (2023), then to NICE (2023), and finally to CORE, an object-centric core metamodel (2025/26) that unifies them on top of OCEL 2.0 ideas. All of these formats store sensor streams **attached to** events or objects, so decision-relevant information exists between events, but the formats do not define decision points.

### Cited Findings
- **SensorStream: An XES Extension for Enriching Event Logs with IoT-Sensor Data.** Grüger, J., Malburg, L., Mangler, J., Bertrand, Y., Rinderle-Ma, S., Bergmann, R., Serral Asensio, E. (author list secondhand). arXiv:2206.11392, 2022. [S] — [arXiv](https://arxiv.org/abs/2206.11392v1)
  - Proposes an XES extension that embeds sensor streams in event logs. The cotton candy and smart factory logs use it.
- **DataStream XES Extension: Embedding IoT Sensor Data into Extensible Event Stream Logs.** Mangler, J., Grüger, J., Malburg, L., Ehrendorfer, M., Bertrand, Y., Benzin, J.-V., Rinderle-Ma, S., Serral Asensio, E., Bergmann, R. 2023. *Future Internet* (MDPI), March 2023. [S] — [DOAJ](https://doaj.org/article/2f912f611deb4bb4b8365d40bb4b0d28); [TUM portal](https://portal.fis.tum.de/en/publications/datastream-xes-extension-embedding-iot-sensor-data-into-extensibl/)
  - The successor to SensorStream. It is the format followed by the newer IoPT datasets.
- **NICE: The Native IoT-Centric Event Log Model for Process Mining.** Bertrand, Y., Veneruso, S., Leotta, F., Mecella, M., Serral, E. ICPM 2023 Workshops, LNBIP, pp. 32–44, DOI 10.1007/978-3-031-56107-8_3. [S] — [dblp](https://dblp.org/rec/conf/icpm/BertrandVLMS23); [KU Leuven Lirias](https://lirias.kuleuven.be/retrieve/3760813f-a1d9-43cd-bc9d-6c8f4f86441f)
  - A native format that merges IoT data with process data while preserving traceability. The authors claim it meets all previously established requirements, and they show on a synthetic log how IoT data explains process anomalies.
- **An object-centric core metamodel for IoT-enhanced event logs (CORE).** Bertrand, Y., Imenkamp, C., Malburg, L., Ehrendorfer, M., Franceschetti, M., Grüger, J., Leotta, F., Mangler, J., Seiger, R., Koschmider, A., Rinderle-Ma, S., Weber, B., Serral, E. arXiv:2506.21300, v1 26 June 2025, v3 26 Jan 2026. [V] — [arXiv](https://arxiv.org/abs/2506.21300)
  - *Summary:* Existing IoT–process data models are fragmented, which hinders data exchange. CORE synthesises their main features into a core model based on common requirements, with a prototype Python implementation evaluated on use cases. According to snippets, a companion BROOM toolbox converts between IoT log formats ([CEUR Vol-4032 paper 33](https://ceur-ws.org/Vol-4032/paper-33.pdf)) [S].
  - *Relevance:* This is the current consensus data model, and the paper explicitly names granularity as the key difference between IoT and process data. Cite it as the state of the art for "OCEL with sensors".
- **OCEL 2.0 event logs page.** — [ocel-standard.org](https://www.ocel-standard.org/event-logs/overview/) [S]

### Gaps
- I did not verify the details of BROOM or of OCED (Object-Centric Event Data) proposals as they relate to IoT.

---

## 4. Event abstraction and activity detection from sensor data

### Takeaway
Event abstraction is the most active IoT-process mining subtopic. Approaches include clustering, HMM segmentation, CEP rules or DSLs, visual analytics, and, more recently, LLM-based labelling. All of them produce discrete events. The thesis can argue that abstraction **discards** the inter-event information that matters for timing interventions.

### Cited Findings
- **Event abstraction in process mining: literature review and taxonomy.** van Zelst, S. J., Mannhardt, F., de Leoni, M., Koschmider, A. *Granular Computing* 6(3), 2021 (online 2020). [S] — [TU/e](https://research.tue.nl/en/publications/event-abstraction-in-process-mining-literature-review-and-taxonom/)
  - A general, not sensor-specific, taxonomy of abstraction approaches, motivated by data recorded at different granularity levels.
- **Clustering Raw Sensor Data in Process Logs to Detect Data Streams.** Ehrendorfer, M., Mangler, J., Rinderle-Ma, S. CoopIS 2023, LNCS, DOI 10.1007/978-3-031-46846-9_25. [S] — [Springer](https://link.springer.com/chapter/10.1007/978-3-031-46846-9_25); [Unpaywall](https://unpaywall.org/10.1007%2F978-3-031-46846-9_25)
  - Clusters sensor values that are stored in process logs in order to identify the underlying data streams.
- **IoT Miner: Intelligent Extraction of Event Logs from Sensor Data for Process Mining.** Brzychczy, E., Jessen, U., Kluza, K., Sriram, S., Vargas Nettelnstroth, M. arXiv:2509.05769, 6 Sept 2025. [V] — [arXiv](https://arxiv.org/abs/2509.05769)
  - A four-stage pipeline (preprocessing, unsupervised clustering, LLM activity labelling, log construction) applied to a load-haul-dump mining machine. It introduces a Similarity-Weighted Accuracy metric.
  - *Relevance:* This is Brzychczy's mining-industry line, and the newest abstraction approach.
- **Sensor2EventLog: Bridging Continuous IoT Data and Process Mining through Eventization.** Authors not verified. Springer LNBIP/LNCS chapter, DOI 10.1007/978-3-032-28110-4_10 (around 2026). [S] — [Springer](https://link.springer.com/chapter/10.1007/978-3-032-28110-4_10); [docs](https://sensor2eventlog.readthedocs.io/en/latest/)
  - Knowledge-guided "machine teaching" with an HMM that segments sensor streams into labelled intervals. It produces logs that enable downstream tasks including predictive monitoring "without relying on fixed time windows", and claims 20–30% higher state abstraction accuracy than purely data-driven methods.
- **A Domain-specific Language and Architecture for Detecting Process Activities from Sensor Streams in IoT (Radiant).** Seiger, R. et al. arXiv:2507.00686, 2025. [S] — [arXiv](https://arxiv.org/pdf/2507.00686v2)
  - An **online** event abstraction DSL and architecture, evaluated in smart manufacturing and healthcare. Its dataset is on [Zenodo 15068153](https://zenodo.org/records/15068153).
- **Activity identification by visualising sensor events.** Weyers, F., Seiger, R., Weber, B. 2022/2023 (BPM workshops, LNBIP). [S] — [Seiger publication list](https://alexandria.unisg.ch/entities/person/Ronny_Seiger/publications)
- **Integrating process management and event processing in smart factories** (systems architecture linking IIoT hardware to a BPMS with CEP). Seiger, R. et al. [S] — [Seiger publication list](https://alexandria.unisg.ch/entities/person/Ronny_Seiger/publications)
- **IoT-enriched event log generation and quality analytics: a case study.** Malburg, Grüger, Bergmann et al. *it – Information Technology*, 2023, DOI 10.1515/itit-2022-0077. [S] — [Trier PDF](https://www.wi2.uni-trier.de/shared/publications/10.1515_itit-2022-0077.pdf)
- **ContinuumConductor: Decentralized Process Mining on the Edge-Cloud Continuum.** arXiv:2512.07280 (Dec 2025). It notes that IoT data is heterogeneous and sits at a lower abstraction level than process event data. [S] — [arXiv](https://arxiv.org/pdf/2512.07280)

### Gaps
- I did not verify Koschmider's own sensor-abstraction papers beyond the reviews (e.g. stationary versus mobile sensor pipelines), nor Rebmann/van der Aa (they have worked on event abstraction in general; I found no IoT-specific paper in this search).

---

## 5. Predictive process monitoring with IoT/sensor context

### Takeaway
IoT-enhanced predictive process monitoring (PPM) exists but is thin. The pattern is consistent: sensor time series are aggregated into features **at event timestamps**, or turned into context events. Predictions are therefore still made at event-aligned prefixes.

### Cited Findings
- **Approaches for IoT-enhanced predictive process monitoring.** Authors not verified. Springer journal with DOI prefix s44311 (likely *Process Science*), 2025. [S] — [Springer](https://link.springer.com/article/10.1007/s44311-025-00011-x)
  - Per the search snippet, it proposes three approaches: (1) add IoT-derived features to events, (2) convert IoT data into context events, (3) analyse IoT and process events jointly. Its case study builds 30 IoT event features from 5 sensor time series.
  - *Relevance:* This is the closest prior work for the predictive half of a PresPM pipeline. Check whether predictions are made only at event prefixes; the snippet suggests yes.
- **Assessing the impact of context data on process outcomes during runtime.** Ehrendorfer, M., Mangler, J., Rinderle-Ma, S. ICSOC 2021. [S] (seen in the reference list of the CoopIS paper) — [Unpaywall, CoopIS 2023 entry](https://unpaywall.org/10.1007%2F978-3-031-46846-9_25)
  - Runtime outcome assessment using context and sensor data. It is very relevant and should be fetched.
- **Analyzing Process Concept Drifts Based on Sensor Event Streams During Runtime.** Stertz, F., Mangler, J., Rinderle-Ma, S. BPM 2020, DOI 10.1007/978-3-030-58666-9_12. [S] — [ACM DL](https://dl.acm.org/doi/10.1007/978-3-030-58666-9_12)
- **Towards IoT-driven predictive business process analytics.** Elhami et al. IEEE COINS 2020. A context-aware PPM method that uses IoT events. [S] — [Sharif repository](https://repository.sharif.edu/resource/480741/towards-iot-driven-predictive-business-process-analytics)
- **Structuring Business Process Context Information for Process Monitoring and Prediction.** Münster WI group. [S] — [Münster](https://www.wi.uni-muenster.de/de/publication/159979)

### Gaps
- I did not search for Banham et al. (context or sensor features in PPM) or for time-series-augmented LSTM/transformer PPM papers.

---

## 6. Prescriptive monitoring and decision-making on IoT-enriched logs (novelty check)

### Takeaway
**I found no paper applying prescriptive process monitoring to IoT-enriched event logs, and none that places decision points at arbitrary sensor readings rather than at events.** The PresPM literature (Shoush and Dumas; the Kubrak et al. "Quo Vadis" survey) addresses *when* to intervene, but only over event-indexed prefixes. The IoT-process mining literature stops at abstraction and prediction. Within this search's limits, the thesis RQ looks novel.

### Cited Findings
- **When to intervene? Prescriptive Process Monitoring Under Uncertainty and Resource Constraints.** Shoush, M., Dumas, M. arXiv:2206.07745, 2022 (BPM 2022 Forum, per background knowledge [S]). [S] — [arXiv](https://arxiv.org/pdf/2206.07745)
  - Ranks ongoing cases by prediction score, uncertainty and causal effect, then triggers interventions to maximise gain under resource limits. Its trade-off between intervening now and later is defined over **event-level states**.
- **Prescriptive Process Monitoring: Quo Vadis?** Kubrak, K., Milani, F., Nolte, A., Dumas, M. (authors from background knowledge). arXiv:2112.01769 (*PeerJ Computer Science*, 2022). [S] — [arXiv](https://arxiv.org/pdf/2112.01769)
  - A survey and framework for PresPM. It classifies methods by intervention frequency (every step versus when a need is detected). Per the snippet, it does not mention IoT or sensor-based decision timing.
- **The cotton candy dataset's own motivation** (a digital twin to optimise heating and spinning actuation) shows practitioner demand for sensor-time control, but no published prescriptive method accompanies it. — [Zenodo 17226615](https://zenodo.org/records/17226615) [V]
- **The IoPT repository paper** lists predictive monitoring, but not prescriptive monitoring, as a target use of the datasets. — [bibbase](https://bibbase.org/network/publication/ehrendorfer-bertrand-malburg-mangler-grger-rinderlema-bergmann-asensio-internetofprocessesandthingsarepositoryforiotenrichedeventlogsinsmartenvironments-2023) [S]
- A targeted search ("prescriptive process monitoring IoT sensor data intervention continuous time decision") returned only generic predictive-maintenance content and the two PresPM papers above. — [search-derived; see arXiv 2206.07745](https://arxiv.org/pdf/2206.07745)

### Inferences
- **Research gaps supported by this evidence:**
  1. **Decision points between events.** All IoT-PM work either abstracts sensors into events or aggregates them into event features. No source treats a sensor reading as a candidate intervention moment.
  2. **PresPM on IoT logs.** There is none, despite the datasets (IoPT) and formats (DataStream XES, CORE) being in place.
  3. **Event-aligned versus continuous decision timing.** This is not compared anywhere. Shoush and Dumas's "when to intervene" is the closest conceptual neighbour, but it is event-indexed.
  4. Abstraction pipelines (Sensor2EventLog, Radiant, IoT Miner) could serve as **baselines that define event-aligned decision points** for the thesis comparison.
- Adjacent fields that do act in continuous time are predictive maintenance, optimal stopping, and control or digital twins. They are outside the process-mining literature. The thesis should position against them briefly; this was not researched here.

### Gaps
- Extended searches were not run on: "causal" or "uplift" work with sensor data in process mining, reinforcement learning for process control on IoT logs, Rinderle-Ma group work on "process-aware" runtime adaptation via CPEE, or 2026 BPM/ICPM workshop proceedings (e.g. a BP-Meet-IoT workshop). These would raise confidence in the novelty claim. **Novelty is therefore "not found in a targeted search", not "proven absent".**
- I did not confirm whether a "BP-Meet-IoT" workshop series exists or what its proceedings contain.
