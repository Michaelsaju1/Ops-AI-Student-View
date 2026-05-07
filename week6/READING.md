# Week 6: Access Control, Data Governance, and Response Monitoring

## The Access Control Problem

Enterprise systems handle sensitive data: salaries, social security numbers, personal health information, financial records. Not all users should see all data.

Access control is the enforcement: given a user with a role, what data can they access? What actions can they take?

Traditional access control is simple: the database has rows with a `role` column, or the API checks a user's permissions before returning data. But RAG agents complicate this:

- The agent retrieves documents from a corpus
- Different users have different permissions on different documents
- The agent synthesizes an answer from retrieved documents
- What if one user can see document A, another can see document B, and the agent accidentally leaks information from both in its response?

## Role-Based Access Control (RBAC)

RBAC is a simple model: users have roles (engineer, HR, finance). Resources (documents, fields) require roles. Access is granted if user's role matches resource requirements.

Example:
```
User: alice (roles: engineer, HR)
Resource: salary_data (required role: finance)
→ DENY
```

Limitations of basic RBAC:
- Doesn't handle resource-specific permissions (Alice is engineer; engineers can access API docs, but not customer data)
- Doesn't express fine-grained rules ("Alice can access this customer's data only if she's their assigned support person")
- Doesn't scale: as resources and roles multiply, the access matrix becomes unwieldy

## Attribute-Based Access Control (ABAC)

ABAC is more flexible: access is granted based on attributes of the user, resource, and context.

Example:
```
Rule: A user can access customer data if:
  - User has role "support"
  - Resource type is "customer_data"
  - User's assigned_customers includes resource.customer_id
  - Access time is during business hours
  - Request is from corporate IP range
```

This is more expressive. Tradeoff: more complex to implement and audit.

## Field-Level and Document-Level Filtering

In RAG agents, filtering happens at two levels:

**Document-level**: When the agent retrieves documents, filter to those the user can access.
- Example: Finance documents should only be visible to finance role
- Implementation: before returning search results, remove documents the user doesn't have permission to see

**Field-level**: Even within an allowed document, certain fields should be redacted.
- Example: A salary document might be accessible to HR, but the salary values themselves should be redacted before returning to a non-HR user
- Implementation: after retrieving a document, scan for sensitive fields and redact them

Example:
```json
{
  "employee_id": "E12345",
  "name": "Alice",
  "salary": 120000,
  "role": "Engineer",
  "ssn": "123-45-6789"
}
```

For role "HR":
- All fields visible

For role "Finance" (can see salary):
- `salary`: visible
- `ssn`, `name`, `employee_id`: redacted

For role "Engineer" (can't see salary):
- All except `salary` redacted

## Audit Logging and Compliance

Audit logging is the record of who accessed what, when, and with what result. It serves multiple purposes:

- **Accountability**: If a breach occurs, determine who accessed sensitive data
- **Compliance**: Regulations (HIPAA, GDPR, SOX) require audit logs as proof of access control
- **Debugging**: If a user complains they can't access something, check the audit log

Critical fields:
- User ID
- Role
- Resource accessed (document, field)
- Action (read, write, deny)
- Timestamp
- Result (success, access denied)
- User's location/IP (for anomaly detection)

Compliance standards:
- [HIPAA requires audit logs of PHI access](https://www.hhs.gov/hipaa/for-professionals/security/audit-controls/index.html) with user, action, outcome, date/time
- [GDPR requires logging of data processing](https://gdpr-info.eu/art-5-gdpr/) and [right to know who accessed your data](https://gdpr-info.eu/art-15-gdpr/)
- [SOX (Sarbanes-Oxley) requires audit trails for financial systems](https://www.sec.gov/cgi-bin/viewer?action=view&cik=1201894&accession_number=0001193125-07-202319&xbrl_type=v)

Logging volume: in a large system, audit logs can exceed the size of the data itself. A 1TB dataset with 1M users making 10 queries each = 10M audit log entries. Compression and archival are necessary.

## PII (Personally Identifiable Information) Detection

PII is information that identifies a person: name, SSN, email, phone, address, credit card, health records. Leaking PII violates privacy law and trust.

Detection approaches:

**Pattern matching**: Use regex to find patterns that look like PII.
- SSN: `\d{3}-\d{2}-\d{4}`
- Credit card: `\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}`
- Email: `[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}`

Limitations: patterns are brittle, false positives/negatives.

**Named Entity Recognition (NER)**: Use NLP model to identify entities (Person, Location, Organization, Money). Relative to regex, more accurate but slower.

**Field-based**: Track which fields contain PII (is this field a salary? SSN?). Before returning, check field metadata.

Field-based is most reliable for structured data like databases. For unstructured text (documents, responses), use a combination of NER and pattern matching.

Best practice: before serving a response to a user, scan for PII. If found, log incident and either redact or reject the response.

## Response Consistency and Monitoring

In agentic systems, the agent's behavior can be non-deterministic: the same query might produce different answers because:
- The LLM is stochastic (temperature > 0 introduces randomness)
- Retrieved documents vary (search results change if corpus or index changes)
- Tool results vary (database queries might return different results if data changed)

Users expect consistency: if I ask the same question twice, I should get the same answer (or at least not contradictory answers).

Monitoring consistency:
1. Run the same query multiple times with the same role and parameters
2. Compare answers (should be identical or semantically equivalent)
3. Alert if answers diverge significantly

Causes of consistency loss:
- **Corpus changed**: New documents added, old documents modified or deleted
- **Search degradation**: Search quality dropped (index corrupted, ranking changed)
- **Tool behavior changed**: Database query now returns different results
- **Access control issues**: Same role now sees different documents (permission settings changed)

Detection: Compute answer hashes, compare. If hashes differ, investigate root cause.

## Metadata and Lineage Tracking

To debug consistency issues, track metadata about every response:
- Which documents were retrieved (document IDs, names, retrieval scores)
- Which fields were visible (before and after filtering)
- Which tools were called and what they returned
- Which fields were redacted and why
- Final response (before and after PII scanning)

Store this metadata with the response. When a user reports an issue, reproduce the query and compare metadata.

## Case Study: Compliance Violation Through Oversharing

Scenario: A TechCorp HR system has an agent. Employees can ask HR questions. The agent has access to payroll data (salaries, bonuses, SSNs).

Access control should limit: most employees see HR policy, benefits info (non-sensitive), but not salaries. Finance team sees salary data.

Failure: An engineer asks "What's the average salary in my department?" The agent retrieves salary documents (all-access), computes average, and returns it. The engineer now knows everyone's salaries (access control was bypassed).

Root cause: the agent wasn't restricted to role-appropriate documents. It retrieved all documents, synthesized an answer, and returned it. The access control was specified but not enforced in the agent's retrieval step.

Prevention: filter documents at retrieval time, not at response time. Agents can't retrieve unauthorized documents to begin with.

## Access Control in Distributed Systems

A single-machine system is simple: load permissions, check before accessing. Distributed systems are harder:

- Permissions might change while the request is in flight (a user's role is revoked mid-request)
- Consistency: does every replica have the same permission table?
- Performance: checking permissions for every field access is slow

Solutions:
- **Permission caching**: Cache the decision "user X, role Y can access document Z" for 5 minutes
- **Fail-safe defaults**: If permission check fails, deny access. Don't continue under uncertainty.
- **Eventual consistency**: Accept that updates to permissions take a few seconds to propagate

[Open Policy Agent (OPA) is a tool that externalizes policy decisions from code.](https://www.openpolicyagent.org/) Instead of embedding access control logic in the application, write policies declaratively and query OPA. Centralized policy simplifies auditing and updates.

## Monitoring for Anomalies

In addition to metrics, monitor for anomalies:

- **Spike in access denials**: Might indicate misconfigurations or attack attempts
- **Unusual role combinations**: User with "engineer" role suddenly accessing "finance" data
- **Bulk data access**: User downloads 1000 documents in 1 minute (normal? or data exfiltration?)
- **Off-hours access**: Engineer accessing customer data at 3 AM (normal? or unauthorized access?)
- **Repeated failures**: User making 100 failed requests in quick succession

Anomaly detection uses baselines (normal behavior) and thresholds (when to alert). [Statistical methods like z-score or isolation forests can detect anomalies automatically.](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.IsolationForest.html)

## References

[Role-Based Access Control (RBAC)](https://en.wikipedia.org/wiki/Role-based_access_control)
- Foundational access control model

[Attribute-Based Access Control (ABAC)](https://en.wikipedia.org/wiki/Attribute-based_access_control)
- More flexible alternative to RBAC

[Open Policy Agent: Decoupling Authorization from Application Code](https://www.openpolicyagent.org/)
- Tool for externalizing and managing access control policies

[HIPAA Security Rule: Audit Controls](https://www.hhs.gov/hipaa/for-professionals/security/audit-controls/index.html)
- Regulatory requirements for healthcare systems

[GDPR and Data Subject Rights](https://gdpr-info.eu/)
- European privacy regulation covering PII protection and access logging

[PII Detection and Classification](https://en.wikipedia.org/wiki/Personally_identifiable_information)
- Overview of what constitutes PII

[Named Entity Recognition for PII Detection](https://huggingface.co/tasks/token-classification)
- Using NLP for identifying sensitive entities

[Audit Logging Best Practices for Compliance](https://www.cisecurity.org/controls/v8)
- CIS Controls framework, including audit logging

[Anomaly Detection in Security](https://www.microsoft.com/en-us/security/business/security-insider/security-insider-detail/anomaly-detection-and-alerting)
- Detecting unusual patterns in access logs

[Isolation Forest Algorithm](https://scikit-learn.org/stable/modules/ensemble.html#isolation-forest)
- Machine learning method for anomaly detection
