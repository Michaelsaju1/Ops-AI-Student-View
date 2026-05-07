# Week 1 - Operational Analysis of a Production AI System

## Before You Start

Read [READING.md](READING.md) first. It introduces the operational thinking framework you'll use for this assignment.

## Assignment

Select a production AI system and **infer** its operational design. Write a 3-page analysis that reasons about what architecture, constraints, and failure modes likely exist, given what you know about the system's requirements.

**What this means:** This is not reverse-engineering secrets or claiming insider knowledge. It's forward inference: given the problem the system solves, given its scale and user requirements, what design would you expect? Why would they build it that way? The goal is sound reasoning, not accuracy about the actual design.

**Operational thinking:** Focus on how the system *works in practice* under real constraints (latency, cost, scale, data quality), not on model accuracy or algorithm sophistication. A student who reasons "they probably use batch prediction because of cost constraints" demonstrates better operational thinking than "they use gradient boosting."

## System Selection

Choose a system with:

- **Clear user behavior**: you understand what users do and how they know if it works
- **Published information available**: the company has written about infrastructure, given talks, filed patents
- **Interesting constraints**: the system has real operational challenges (scale, latency, cost, or data complexity)

Good choices (companies have published heavily about these):

- Spotify recommendations
- Google Maps ETA
- Uber surge pricing & ride matching
- Netflix recommendations
- LinkedIn feed ranking
- Gmail spam filter
- Amazon product recommendations
- TikTok content ranking

Systems with less published information or fewer constraints will be harder. Consult instructor before choosing something outside this list.

## Where to Find Published Information

You're not reverse-engineering secrets. You're finding what companies have already told the public. Search for:

- **Engineering blogs**: Google "[company] ML infrastructure" or "[company] blog engineering"
- **Tech talks**: YouTube, engineering conferences (Uber Eng, Netflix Tech, Google Cloud Next, etc.)
- **Patents**: patents.google.com - often reveals technical approaches years before papers
- **Investor presentations**: Earnings calls, SEC filings, shareholder letters (mentions of ML investment, scale)
- **Academic papers by their researchers**: Google Scholar for papers authored by company engineers
- **Product behavior**: What you observe as a user tells you about constraints (latency, staleness, fallback patterns)

**Time allocation**: For well-documented systems (Spotify, Google Maps, Uber), plan 45–60 minutes finding references and 2–2.5 hours analyzing and writing. Systems with less public information may require additional background research.

## Analysis Components

Your report must address all 7 dimensions. Use the READING.md framework:

**Allocate the 3 pages based on reasoning depth, not equally.** Some dimensions will be obvious for your system; others will need deeper analysis. Example: If your system's architecture is straightforward (batch prediction), spend less there and go deeper on data dependencies or failure modes. If constraints are complex, allocate more pages there.

1. **Users & Interaction** - Who depends on this system? What decisions do they make based on its output? How quickly do they notice when it's wrong? (Example: Spotify users notice bad recommendations immediately; consequences are mild. Google Maps users notice late ETAs in the moment; consequences are real.)
2. **Data Sources** - What feeds the system? Volume? Latency? Completeness? What happens if a source goes offline or changes schema? (Example: Maps relies on GPS from phones, sparse in rural areas, delayed by 5+ minutes.)
3. **Models/Algorithms** - What approach likely works given the constraints? Why? What are known failure modes? (Example: Don't say "they use neural networks." Say "they probably use gradient boosting because it's fast to serve, interpretable for debugging, and handles sparse features well.")
4. **System Architecture** - How do requests flow? Where is caching necessary? What are the sequential dependencies? What breaks if a component fails? (Example: If feature store is down, can the system return cached predictions?)
5. **Constraints & Failure Modes** - What are the hard limits (latency SLA, cost per prediction, uptime requirement)? What fails first when constraints are violated? (Example: If latency SLA is 100ms and model inference takes 50ms, you have only 50ms for feature lookup. This is a real constraint that shapes architecture.)
6. **Monitoring** - What signals indicate health? How do you detect silent failures (system returns bad predictions but doesn't crash)? What metrics matter for operations? (Example: Not just accuracy. Also: is the model always predicting the same thing? Has input distribution changed? Are certain user segments degrading?)
7. **Business Value** - What is the system actually optimizing for? Where might incentive misalignment happen? (Example: A recommendation system optimizing purely for engagement can be gamed by showing outrage content. What's the actual business objective?)

## Format

- 3 pages (±0.5 acceptable)
- PDF, 11pt, 1" margins, single-spaced
- Optional: architecture diagram
- File: `[Name]_week1_operational_analysis.pdf` on Canvas

## Grading

| Criterion                                                                 | Weight |
| ------------------------------------------------------------------------- | ------ |
| All 7 components addressed                                                | 30%    |
| Operational thinking (system > model; focus on constraints, not accuracy) | 30%    |
| Clear writing, logical flow, proper citations                             | 20%    |
| Identifies non-obvious problems; reasons about tradeoffs                  | 20%    |

90–100: Insightful, shows operational complexity
80–89: Competent coverage, some insights
70–79: All components, surface-level analysis
<70: Missing components or insufficient depth

## How to Make Good Inferences

**Know what you're inferring from:**

- Public tech talks and blog posts (Uber's Michelangelo, Airbnb's Chronon, Google's papers)
- System behavior (if it serves in <100ms, what architecture allows that?)
- Constraints (1 billion users at $0.001 per prediction means infrastructure is cost-critical)
- Industry best practices (what does a system at this scale typically do?)

**When you don't know something, reason about it:**

- Don't say "I don't know if Spotify caches recommendations." Say "Given that they serve millions of users with <500ms latency, they probably cache heavily because live model inference wouldn't be fast enough. Here's why."
- Don't claim insider knowledge. Say "Based on public information about their scale, I infer..."

**What to research:**

- Earnings calls and investor presentations (mentions of infrastructure, investment in ML)
- Engineering blog posts and tech talks by company engineers
- Academic papers or industry conference talks
- Patent filings (can reveal technical approaches)
- Product behavior (reverse-infer from what users see)

**Focus on reasoning, not facts:**

- You're learning to think about systems operationally
- Right answer is not the goal; good reasoning is
- A student who infers "they probably use batch prediction because of cost constraints" shows better thinking than "they use gradient boosting"
- Consider humans: where do people need to intervene?

## Common Mistakes to Avoid

**Focusing on model accuracy instead of operations:**

Weak: "Spotify uses a 95% accurate collaborative filtering model"
Better: "Given millions of users and <500ms latency requirement, they probably cache pre-computed recommendations and use batch retraining daily"

**Making claims without reasoning:**

Weak: "They use a neural network"
Better: "They probably use a neural network because of high-dimensional features, but it must be distilled or cached to meet latency SLAs"

**Ignoring constraints:**

Weak: "The system predicts demand"
Better: "The system must predict demand in <100ms, which means feature lookup is cached and model inference is fast—probably simpler than optimal"

**Forgetting about failure and degradation:**

Weak: "The system is accurate"
Better: "The system is accurate most of the time, but when real-time data lags >10 minutes, it probably falls back to historical patterns"

**Analyzing only the technical side:**

Weak: Entire analysis is about model type and architecture
Better: "The system optimizes for engagement, but that can misalign with user satisfaction. Humans probably filter out harmful content"

**Being too vague:**

Weak: "The system has monitoring"
Better: "The system monitors accuracy on recent data (24-hour ground truth lag), latency percentiles, and input distribution. Likely alerts if any segment drops >10% accuracy"

## Sample Excellent Analysis

Here's what exceptional work looks like. This is a short excerpt from a **Constraints & Failure Modes** section (the kind that scores 90–100%):

---

*Spotify's latency SLA is likely <500ms for recommendation generation (standard for consumer music apps). This creates a hard constraint: if feature computation + model inference + result formatting exceeds 500ms, the UI lags and users perceive slowdown.*

*Given this constraint, the system probably cannot run complex deep neural networks at request time, even if they're more accurate. Instead, they likely use a two-tier approach: precomputed embeddings (batch offline) serve most requests through cached lookups, with a lightweight online model (gradient boosting, neural network distillation) handling personalization. This explains why they can afford high accuracy without unacceptable latency.*

*The failure mode most likely to occur is cache miss: if a user is new (no cached recommendations), the system must compute recommendations in <500ms. This is the hard case. Spotify probably handles this by falling back to popular-items-for-your-genre rather than trying personalization. Silent failure risk: if the fallback is never tested, it might silently degrade the experience for new users, but metrics would only show this if they segment by user age.*

*A second failure mode is batch staleness: if the nightly retraining job fails or takes too long, yesterday's embeddings serve stale recommendations. Mitigation: versioning (keep two versions) so recommender can serve old embeddings while new ones compute in the background.*

---

**What makes this work exceptional:**

- Identifies the constraint first (latency SLA), then reasons forward ("this rules out X, forces Y")
- Infers architecture from constraint (two-tier, not single deep model)
- Names specific failure modes, not generic ones ("cache miss for new users," "batch staleness," not "models degrade")
- Quantifies where possible ("<500ms," "nightly," "two versions")
- Explains mitigation and tradeoffs (fallback is safe but less personalized)
- Acknowledges what it doesn't know ("probably," "likely")
- Identifies the non-obvious risk (silent degradation for new users that metrics miss)

This goes beyond listing what the system does. It shows *why the system works that way given its constraints*, what could break, and how failures might hide. That's operational thinking.

---

## Due

End of Week 1 (exact date in syllabus; plan to complete by end of week)
