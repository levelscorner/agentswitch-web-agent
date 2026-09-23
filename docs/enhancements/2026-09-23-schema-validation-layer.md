# Enhancement — one shared input-validation layer at the schema level

- **Area:** Website (applies platform-wide)
- **Type:** enhancement (hardening / architectural)
- **Reported by:** Team 09
- **Submit via:** the bug-report button, description prefixed `[ENHANCEMENT]`
- **Relates to:** bugs N158, N159, N160 (all the same class: a field accepting a value it should reject)

## Paste-ready description

> **[ENHANCEMENT] Add schema-level input validation so the "field accepts a bad value" class of bugs is closed at the source, not field by field.**
>
> Context: N158, N159 and N160 are three separate bugs but one root cause — fields accept values they should reject, because validation is done (inconsistently) per field instead of declared on the schema. New fields keep inheriting the same gap.
>
> Proposal — declare and enforce these constraints on the entity schema, so the engine applies them everywhere:
> 1. **URL fields:** scheme allowlist (http, https, mailto, tel). Blocks `javascript:` and other unsafe schemes (N158).
> 2. **Numeric fields:** min/max bounds (e.g. `sitemap_priority` 0–1, scores 0–100, no negatives) (N160).
> 3. **Cross-field rules:** e.g. a redirect's `from_path != to_path` (N159).
> 4. **System-owned fields:** mark counters read-only to clients (`view_count`, `hit_count`) so they can't be set or faked (N160).
> 5. **Stored HTML/JSON:** escape/sanitize on render so `json_ld_override` and link fields can't execute on the public `/site/` pages (N158).
>
> Benefit: one change closes the whole class instead of patching each field, and every future field inherits the protection.
>
> Scope: schema/validation engine; primary impact on the website domain.
