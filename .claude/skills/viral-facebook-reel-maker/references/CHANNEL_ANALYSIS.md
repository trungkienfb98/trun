# Reference-channel analysis

Analyze only material the user is authorized to view. Record visible evidence and label inference explicitly.

## Capture per post

- URL or stable identifier
- Publish date and post type
- Full accessible text
- Reactions, comments, shares, and views when visible
- Topic, audience problem, and hook structure
- Formula: comparison, roundup, tutorial, AIDA, list, mistake, before/after, or opinion
- Ending style, visual format, and text density

## Rank candidates

Prefer a rate normalized against the channel baseline when follower count and reach are available. Otherwise use a transparent heuristic and retain raw metrics:

`score = reactions + 2*comments + 3*shares + 0.02*views`

Treat the score as a selection heuristic, not proof of causation. Favor evergreen posts that can stand alone in a short visual treatment. Exclude private, sensitive, copied, disputed, or context-dependent material.

## Learn without cloning

Extract topic mix, pacing, hook type, information architecture, visual hierarchy, and publishing rhythm. Do not copy distinctive wording, personal anecdotes, identity, logos, private footage, or unverified claims.

Save analysis to `08_PHAN_TICH_KENH/reference_analysis.json` and candidates to `04_NOI_DUNG`.
