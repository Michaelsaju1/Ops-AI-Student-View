# Week 1: The Operational View of Production ML Systems

## Context: Why This Matters Now

Most ML education focuses on model building. But industry evidence shows 85% of ML models never move past prototyping. The gap is not accuracy generally, but operationalization.

Production ML systems operate under hard constraints: latency budgets, cost budgets, availability requirements. These constraints are not obstacles to overcome; they are the fundamental design parameters. A model that is theoretically optimal but misses latency SLA is worthless in production.

This week asks a different question: not "How do we maximize accuracy?" but "Given that this system will fail, given that people depend on it, given incomplete information and finite budgets, how does this system actually work?"

## The Seven Structural Dimensions

Research on production ML systems identifies consistent structural elements that determine whether systems work or fail. These are the same 7 dimensions you will use in your assignment analysis.

### 1. Users & Interaction

Production ML systems exist to help people make decisions. Understanding who depends on the system and how they use it is where operational analysis begins.

Key questions:

- **Who uses the system?** End-users? Other systems? Internal teams? Support agents?
- **What decisions do they make based on its output?** Do they blindly trust it, or verify it? How much do they rely on it?
- **How quickly do they notice when it's wrong?** A Spotify recommendation is noticed immediately but consequences are mild. A Google Maps ETA is noticed in the moment with real consequences (you're late). An email spam filter might silently fail for days before you realize important mail was missed.
- **What is the cost of failure?** Financial loss? Safety risk? Reputation damage? User annoyance?

Understanding these determines how much monitoring and validation you need, what SLAs matter, and how serious silent failures are.

### 2. Data Sources

Production systems depend on data sources. These sources have properties that determine reliability and shape system design:

- **Latency**: Data arrives with delay. GPS signals in Google Maps have ~5-10 minute lag. ETL pipelines in batch systems run daily. Real-time Kafka streams have millisecond latency but eventual consistency. This delay affects how fresh predictions can be.
- **Completeness**: Data is never fully observable. We see only completed transactions, not rejected requests. Only GPS from users running the app, not all vehicles. Only feedback that users explicitly provide. Missing data means the system has blind spots.
- **Dependencies and coupling**: Feature A is computed from source B, but then C depends on A without B knowing. When B changes schema, C breaks. [Sculley et al.&#39;s seminal paper on technical debt](https://proceedings.neurips.cc/paper_files/paper/2015/file/86df7dcfd896fcaf2674f757a2463eba-Paper.pdf) identifies this as a primary source of production fragility.
- **Drift**: Statistical properties of data change over time. Research distinguishes covariate shift (input distribution changes) from concept drift (label distribution or target function changes). Both occur inevitably in production and are covered under Constraints & Failure Modes below.

Modern platforms like [Airbnb&#39;s Chronon](https://www.infoq.com/news/2024/04/airbnb-chronon-open-sourced/) address hidden dependencies by requiring features to be defined once, with both offline (training) and online (serving) pipelines generated automatically. Before such tools, teams spent months manually implementing these pipelines.

### 3. Models/Algorithms

What approach should the system use? This depends entirely on constraints, not theoretical optimality.

Different algorithm choices have different operational characteristics:

- **Gradient boosting**: Fast inference, interpretable, handles sparse features well. Good for latency-sensitive systems with complex feature spaces.
- **Neural networks (deep)**: Can handle high-dimensional nonlinear relationships, but slower inference and harder to debug. Requires careful tuning.
- **Neural networks (distilled/small)**: Fast inference with some accuracy sacrifice. Used when you need neural network capability but have latency constraints.
- **Simple rules/heuristics**: Fastest inference, most interpretable, but limited accuracy. Used as fallbacks or for simple decisions.
- **Ensemble methods**: Combine multiple models for higher accuracy, but slower inference.

**The key insight**: The algorithm is not chosen for theoretical optimality, but for what works given operational constraints. A student who reasons "they probably use gradient boosting because inference must be <100ms and interpretability matters for debugging" demonstrates better operational thinking than "they use neural networks because they're most accurate."

Algorithm-specific failure modes:

- Gradient boosting: Can fail if feature distributions shift significantly (covariate drift)
- Neural networks: Can fail unexpectedly on out-of-distribution data; hard to debug why
- Ensembles: Individual model failures can cascade, or models can give contradictory predictions

### 4. System Architecture

How do requests flow through the system? Architecture patterns determine all downstream operational decisions.

Production ML systems use three primary serving patterns, each with different tradeoff profiles:

**Batch prediction**: Compute predictions for large datasets on a schedule, store results, serve via lookup. Advantages: flexible compute budget, can use cheaper infrastructure, predictable cost. Disadvantages: predictions are stale (hours or days old), cannot adapt to individual user context at request time.

**Online serving**: Predictions computed at request time via API. Advantages: always fresh, can personalize based on individual context. Disadvantages: must meet latency SLA (typically <100ms for consumer applications), requires fast inference and feature lookup infrastructure.

**Hybrid**: Some predictions precomputed and cached, others computed at request time. Example: Uber's Michelangelo platform started with batch prediction, added real-time prediction later as business requirements evolved.

[Uber&#39;s engineering blog documents](https://www.uber.com/us/en/blog/scaling-michelangelo/) how real-time ML is "challenging to get right" because most existing data tools are built for either offline ETL or online streaming - few handle the hybrid capabilities required by production systems. The platform evolved incrementally: first batch training and predictions, then feature store, then low-latency serving, then deep learning workflows.

**Why architecture matters operationally**: Architectural choice cascades into all downstream decisions. Acceptable latency determines whether you can run complex models at request time. Cost budget determines whether you can afford real-time serving. Availability requirement determines how much redundancy you need.

### 5. Constraints & Failure Modes

ML systems fail differently than traditional software. A traditional system fails visibly: it crashes, returns errors, goes down. ML systems fail silently: they return predictions with high confidence even as those predictions become worthless.

**Hard constraints** (what the system must meet):

- **Latency SLA**: Prediction must return within X milliseconds. If this fails, UI lags or the system is useless.
- **Cost budget**: Cost per prediction must be below X cents. If model inference is too expensive, profitability collapses.
- **Availability**: System must be up X% of the time. Availability failures cause revenue loss and user frustration.

**Silent failure**: The system keeps running. Logs show no errors. But the underlying data or model is wrong, and decisions made on bad predictions compound over time.

Common failure modes:

**Data drift failure**: Input distributions shift. A model trained on 2020 traffic patterns is applied to 2026 traffic. A model trained on historical credit patterns encounters a new fraud pattern. The model was never designed for this regime, but it still outputs predictions. [Statistical tests like the Kolmogorov-Smirnov test and Population Stability Index (PSI)](https://www.evidentlyai.com/ml-in-production/data-drift) quantify distribution shift, but measuring these requires instrumentation.

**Concept drift failure**: The relationship between inputs and outputs changes. This is subtler. The features haven't changed, but what they predict has. Example: a model predicts restaurant demand based on historical patterns. But a pandemic changes how restaurants operate. The historical relationships are broken. Or: a recommendation system optimizes for engagement, but engagement patterns shift as user behavior adapts.

Concept drift is harder to detect because it requires measuring model performance against ground truth, which is often only available with delay.

### 6. Monitoring

In practice, many organizations lack comprehensive monitoring for ML systems. Some rely on custom-built solutions that do not generalize. This gap between need and practice creates operational risk.

The difference between **monitoring** and **observability** matters:

- **Monitoring** measures known metrics (accuracy, latency, throughput). You define what to measure, then measure it.
- **Observability** is the ability to ask arbitrary questions about system behavior after failures occur. It requires comprehensive instrumentation and logging so you can investigate "why did this fail?" without having pre-defined all possible failure modes.

Good monitoring for ML systems includes:

- **Data metrics**: distributions of input features, presence of null values, cardinality of categorical features
- **Model metrics**: predictions produced, prediction distribution (is the model outputting the same value for everything?), confidence scores
- **Performance metrics**: accuracy measured on recent data with ground truth, segmented by important subgroups (by user, by geography, by time of day)
- **System metrics**: latency (p50, p95, p99), throughput, error rate, cost per prediction
- **Business metrics**: whatever the system is actually optimizing for (engagement, revenue, user retention)

**The critical practice is segmentation**: measuring not just globally but by meaningful subgroups. A system that performs well globally can be performing terribly for a specific geography or user demographic. You won't see this without instrumentation.

### 7. Business Value

ML systems are built to optimize a metric. But metrics can be gamed or can optimize for the wrong thing.

**Incentive misalignment example**: A recommendation system optimizes for engagement (clicks, watch time). This can be achieved by recommending outrage content, conspiracy theories, or sensationalism- maximizing clicks but degrading user experience and trust. Accuracy improved; business value declined.

[Sculley&#39;s technical debt paper identifies this as boundary erosion](https://proceedings.neurips.cc/paper_files/paper/2015/file/86df7dcfd896fcaf2674f757a2463eba-Paper.pdf): the system boundary becomes unclear. Is the system optimizing for accuracy? Engagement? Revenue? User retention? When these conflict, which wins?

Production systems require explicit decisions about what is being optimized. Airbnb's dynamic pricing must balance revenue against host fairness and platform risk - no pure technical solution exists. The metric chosen is a business decision, not an engineering one.

## Supplementary: Retraining and Model Staleness

A model trained once becomes stale. Data changes. User behavior changes. The relationship between features and outcomes drifts. But retraining introduces risk: a new model might be worse than the old one, or better on historical test data but fail on unseen patterns.

**When do you retrain?** Common triggers:

- **Performance drops**: Accuracy measured on recent data falls below threshold
- **Data drift detected**: Input distribution has shifted significantly
- **On schedule**: Weekly, daily, hourly - depends on data freshness requirements
- **After significant events**: Policy change, new feature launched, external shock

**The retraining problem**: You can validate a new model against historical test sets, but you cannot know if it will work on data you have not yet seen. [Uber&#39;s platform enforces rigor in retraining:](https://www.uber.com/us/en/blog/enhancing-the-quality-of-machine-learning-systems-at-scale/) versioning, testing, and deployment are enforced. The system doesn't automatically deploy new models. It validates them first.

**The practical approach**:

- Trigger retraining on clear signals (performance drop, drift detected)
- Validate the new model carefully against recent data
- Deploy gradually: canary deployment (serve new model to small user segment), shadow mode (run new model in parallel, compare), or blue-green (switch traffic between old and new)
- Monitor closely after deployment
- Keep multiple versions available so you can rollback if the new model fails

**Common failure mode**: Retraining job fails or takes too long. Yesterday's model is still in production, getting staler. Mitigation: keep two versions in production so recommender can serve old predictions while new model is training in background. Trade staleness against freshness.

This is where humans intervene: someone notices model quality dropped, investigates whether it's data drift or concept drift, triggers retraining if needed, validates, and deploys.

## The Technical Debt Framework

[Sculley et al. (Google, 2015) introduced the concept of technical debt specific to ML systems.](https://proceedings.neurips.cc/paper_files/paper/2015/file/86df7dcfd896fcaf2674f757a2463eba-Paper.pdf) Traditional software has technical debt (poorly written code, architectural shortcuts). ML adds:

- **Data dependencies**: features depend on upstream data sources, creating invisible coupling
- **Feedback loops**: system predictions change user behavior, which changes data, which changes what the system should predict. Hard to track causality.
- **Undeclared consumers**: multiple downstream systems depend on model outputs without the model owner knowing
- **Data cleaning logic**: increasingly complex logic for handling edge cases, nulls, outliers, accrues over time with no tests
- **Experimental debt**: many models are tried but only winners are deployed; loser code is deleted but accumulated experimental approach is forgotten

The argument: ML systems incur more technical debt than traditional software because the model is only 5% of the system. The other 95% is infrastructure, pipelines, and monitoring. This 95% is where problems hide.

## A Full Example: Uber's Michelangelo

Uber's ML platform (Michelangelo) provides a case study in how production constraints shaped architectural decisions:

**Initial problem**: Different teams were building ML systems independently. Each team reimplemented core infrastructure (feature computation, training, serving). Duplicated effort. Different standards.

**Architecture**: Michelangelo provides:

- Centralized feature store: features defined once, reused across models
- Batch training: distributed training on historical data
- Real-time serving: low-latency predictions for Uber's core systems
- Monitoring: automated model quality tracking

**Key lessons documented by Uber**:

1. Real-time ML is harder than batch: most tools handle one or the other, not both. Uber had to build custom infrastructure.
2. Model quality requires automation: manually retraining, validating, and deploying models does not scale. They automated the full lifecycle.
3. Decentralized teams with centralized platform: teams own their models, but platform enforces standards (versioning, testing, deployment).
4. Gradual evolution: started with batch prediction, added features incrementally as business needs evolved.

The implication: production ML architecture is not determined by the algorithm choice. It is determined by operational requirements: latency SLA, availability SLA, cost budget, scale, team structure.

## References and Further Reading

**Core papers on production ML systems:**

[Hidden Technical Debt in Machine Learning Systems](https://proceedings.neurips.cc/paper_files/paper/2015/file/86df7dcfd896fcaf2674f757a2463eba-Paper.pdf) (Sculley et al., Google, NeurIPS 2015)

- Foundational paper defining the landscape of ML-specific technical debt.

**Company-specific case studies on production systems:**

[Scaling Machine Learning at Uber with Michelangelo](https://www.uber.com/us/en/blog/scaling-michelangelo/)

- Documents how a large company built centralized ML infrastructure, including lessons learned.

[Airbnb&#39;s Chronon: Open Source ML Feature Platform](https://www.infoq.com/news/2024/04/airbnb-chronon-open-sourced/)

- How Airbnb reduced feature engineering time from months to days by building a unified feature platform.

[ML System Design Patterns](https://github.com/mercari/ml-system-design-pattern) (Mercari)

- Catalog of design patterns for production ML, covering data, model, and training patterns.

[Architecting ML-enabled systems: Challenges, best practices, and design decisions](https://www.sciencedirect.com/science/article/pii/S0164121223002558)

- Academic survey of 35 design challenges and 42 best practices when building ML systems.

**On data drift and model degradation:**

[Understanding Data Drift and Model Drift](https://www.evidentlyai.com/ml-in-production/data-drift)

- Practical guide distinguishing covariate drift from concept drift, with detection methods (KS test, PSI).

**On monitoring and observability:**

[A Guide to Machine Learning Model Observability](https://encord.com/blog/model-observability-techniques/)

- Covers the difference between monitoring and observability, with practical implementation approaches.

[ML Model Monitoring to Prevent Production Disasters](https://galileo.ai/blog/ml-model-monitoring)

- Detailed guide on detecting silent failures and degradation in production models.

[AI Observability: The Cure for AI Silent Failure](https://feedzai.com/blog/ai-observability-the-cure-for-silent-failure/)

- Explains why ML systems fail silently and how observability prevents it.

---

## Applying This to Your Assignment

Your assignment asks you to analyze a production AI system using these seven dimensions:

1. **Users & Interaction** - Who depends on this system? What decisions do they make based on its output? How quickly do they notice when it's wrong? What's the cost of failure?
2. **Data Sources** - What feeds the system? Volume? Latency? Completeness? Dependencies? What happens if a source goes offline or changes?
3. **Models/Algorithms** - What approach likely works given the constraints? Why that approach over others? What are the known failure modes?
4. **System Architecture** - How do requests flow? Where is caching necessary? What are the sequential dependencies? What breaks if a component fails?
5. **Constraints & Failure Modes** - What are the hard limits (latency SLA, cost per prediction, uptime requirement)? What fails first when constraints are violated? What does silent failure look like?
6. **Monitoring** - What signals indicate health? How do you detect silent failures (system returns bad predictions but doesn't crash)? What metrics matter for operations?
7. **Business Value** - What is the system actually optimizing for? Where might incentive misalignment happen?

You will not know all answers. That is expected. Make educated guesses based on the business context, scale, and user requirements. The point is not to reverse-engineer the exact system; it is to think operationally about how it works and what could break.

Your 3-page analysis should synthesize these dimensions into a coherent narrative about why the system works the way it does, what its operational constraints are, and what failure modes are most likely.
