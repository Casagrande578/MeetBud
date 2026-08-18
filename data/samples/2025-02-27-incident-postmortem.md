---
date: 2025-02-27
title: Postmortem — Search Index Outage
participants: [Diego Ramirez, Aisha Bello, Marcus Owens]
---

# Postmortem — Search Index Outage

Diego walked through the timeline of the Feb 25 outage: search index went unavailable
for 47 minutes due to a memory leak in the reindexing job introduced in last week's
deploy. Root cause identified as an unbounded cache in the tokenizer.

No customer data was lost. About 3% of daily active users hit degraded search results
during the window; no full outage of core product features.

## Decisions
- Add a bounded LRU cache to the tokenizer, cap at 500MB.
- Add alerting on reindex job memory usage going forward — none existed before.
- Delay next reindex-related deploy until the fix is verified in staging for 48 hours.

## Action items
- Diego: implement bounded cache fix, target 2025-03-01
- Aisha: add memory usage alerting to the monitoring dashboard
- Marcus: draft customer-facing incident summary if any customers ask
