---
name: source-legality-check
description: Checks whether a website or its API is safe and legal to use as a data source for scraping or integration -- e.g. when building a bot that aggregates job listings, real-estate listings, or any other data from a third-party site. Use this proactively whenever the user wants to add a new website/country/source to an existing scraper or bot, is evaluating a site they found, or asks "can we use this site", "is this legal to scrape", "how do we get data from X", or is expanding a project (job search, real estate, price tracking, etc.) into a new country or new target site. Produces a clear verdict (safe to use / needs written permission / avoid) with reasoning, based on robots.txt, Terms of Service, community-documented APIs, and a live test request.
---

# Source Legality Check

Before writing a single line of scraper/integration code against a new
website, spend a few minutes establishing whether it's actually okay to use
as a data source. Skipping this step is how a project ends up needing to be
rewritten later (or, worse, generates a legal problem) -- it's much cheaper
to find out up front that a site explicitly forbids automated access than
to build against it and find out after.

This workflow was developed live while building two Telegram bots (job
search bots for Denmark and Germany): Jobindex.dk, Jobnet.dk, and
Germany's Bundesagentur für Arbeit turned out to be safe to use (open
robots.txt, no anti-automation clause, and for the two undocumented ones, a
community-maintained reverse-engineered API already existed). BoligPortal.dk
(a Danish rental listings site) was rejected outright -- its robots.txt
explicitly states scraping isn't permitted without written consent.

## The four checks

Run all four before giving a verdict. Each one alone can be misleading --
e.g. a site can have an open robots.txt but a ToS that forbids automation
anyway, or vice versa.

### 1. robots.txt

```
curl -sS "https://<domain>/robots.txt" -A "<a normal browser user-agent>"
```

Look past the `Disallow:` directives (those are routine -- e.g. blocking
`/login` or `/admin` from search engines) for **explicit prose forbidding
automated use**. That's a different, much stronger signal than a technical
disallow rule. Real example that should stop you cold:

> `# Note: Crawling BoligPortal is not permitted without written permission.`
> `# See the terms and conditions in our Data and Privacy Policy...`

Compare to a genuinely open one (Denmark's Jobindex, Germany's
Bundesagentur für Arbeit): just routine `Disallow:` lines, or none at all,
with no explanatory text about crawling being forbidden.

If robots.txt links to a Terms/Data Policy page for more detail (as
BoligPortal's does), fetch that page too -- don't stop at the robots.txt
file itself.

### 2. Community-documented APIs

Many official-feeling sites, especially government portals, have no
*official* public API but a well-known *unofficial* one that a community
has already reverse-engineered and documented -- meaning you don't need to
reverse-engineer it yourself, and its existence + popularity is itself a
weak signal that using it hasn't caused problems for others.

Search for:
- `"<site name>" API github`
- `"<site name>" reverse engineered api`
- `"<site name>" unofficial api`
- Check GitHub orgs that catalog government/public APIs for the relevant
  country (e.g. `bundesAPI` for Germany's federal government services).

Real example: `bundesAPI/jobsuche-api` on GitHub fully documents the
Bundesagentur für Arbeit's undocumented mobile-app API -- endpoints,
auth header, everything -- saving the work of finding it independently.

If you find an undocumented-but-used API, treat it like the Jobnet.dk BFF
endpoint used elsewhere in this codebase: real, works, but can change or
get blocked without notice, so any integration should fail gracefully
rather than crash the whole feature when it does.

### 3. Terms of Service / Data & Privacy Policy

Even with an open robots.txt, skim the site's ToS or data policy for
language like "automated access," "scraping," "crawling," "bots," or
"systematic extraction." Some sites bury the real restriction here instead
of in robots.txt.

### 4. Live test request

Confirm the source actually, concretely works before building anything on
top of it -- don't take documentation (community or official) on faith.

```
curl -sS "<the actual endpoint or search URL>" -H "..." | head -c 2000
```

Check that the response contains real, current data (e.g. today's date
somewhere in a listing, plausible content) and not an error page, a CAPTCHA
wall, or a 403 that a browser User-Agent happens to paper over.

## Verdict

State one of these three plainly, with the reasoning that led there:

- **✅ Safe to use** -- open robots.txt, no ToS restriction found, live
  request returns real data. Proceed with the integration, but note if the
  API is undocumented/unofficial (so failures are expected and handled
  gracefully rather than surfacing as crashes).
- **⚠️ Needs written permission** -- explicit prohibition found (robots.txt
  and/or ToS), but the data would be genuinely valuable. Recommend emailing
  the site owner to ask for permission or an official API/partner feed,
  rather than building around the restriction. Don't suggest scraping
  anyway, using a third-party scraper service that does the same thing, or
  any other way of working around an explicit "no."
- **❌ Avoid** -- explicit prohibition and no realistic path to permission
  (e.g. no contact channel, or the ask is out of scope for the project).
  Suggest looking for an alternative source that serves the same purpose
  legitimately, or dropping that particular source.

## Example output

```
Перевірив BoligPortal.dk для моніторингу оренди:

1. robots.txt: явна заборона -- "Crawling BoligPortal is not permitted
   without written permission" з посиланням на Data and Privacy Policy.
2. Community API: не знайшов офіційного, лише платні сторонні скрапери
   на Apify -- вони так само обходять цю заборону.
3. ToS: підтверджує заборону, посилається на copyright law.
4. Live test: не тестував, бо пункти 1-3 вже дають чіткий вердикт.

Вердикт: ⚠️ Потрібен письмовий дозвіл. Не рекомендую скрапити чи
використовувати сторонні скрапери в обхід. Варіанти: написати
BoligPortal напряму з проханням про partner API, або знайти інший
портал оренди з відкритим доступом.
```

## Notes

- This check is about the *site's own rules*, not a legal opinion on GDPR
  or other data-protection law -- those are separate questions (e.g. even
  a scrapeable site can still hand you personal data that then needs to be
  handled carefully once it's yours).
- Re-run this check when reusing the workflow for a new country/site --
  don't assume one country's version of a similar site (e.g. one nation's
  job portal being open) tells you anything about another's.
