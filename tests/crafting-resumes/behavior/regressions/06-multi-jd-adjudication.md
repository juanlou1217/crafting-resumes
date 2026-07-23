# 06 Multi-JD Adjudication

Candidate output SHA-256: `6eece08b871942e1662f049253becdeab4b8cb89bce6ed845be89beb429fc662`.

Aggregation rule: `strict-majority-v1; selected by lowest canonical SHA-256 among judgments agreeing with the majority`.

Selected judgment: `06-multi-jd-adjudicator-a.json` (`a769682a85ffdfccdcad416ffbb52a0db73d46e20ca91bcd332e3fb9811fa18a`).

The first blind judge passed every frozen `must`, `must_not`, hard-fail, and qualification criterion, but returned `fail` after treating interview questioning as applicable and scoring both interview information gain and HR scan quality at 2.

Two further independent blind adjudicators reviewed the same randomized output without seeing the first result. Both returned `pass`, scored HR scan quality at 3, and treated interview information gain as `N/A` because this case requests two evidence-safe direction versions rather than an interview round. This agrees with the frozen multi-JD contract: ordinary `weak`/`gap` items do not force a question, and sparse user wording must not be expanded into invented actions.

The candidate output remains unchanged. The final manifest adopts adjudicator A's complete gates, scores, reason, and result because A has the lowest canonical JSON SHA-256 among the two judgments agreeing with the strict majority. The original judgment and both independent adjudications are preserved beside this disposition.
