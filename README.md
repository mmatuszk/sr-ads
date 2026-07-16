# SR Ads

This repository contains paid-media analysis, platform-specific management
tools, shared audience workflows, and the decision record for live advertising
changes.

## Organization Principle

Code and records belong to the narrowest channel or shared workflow that owns
them:

- Google Ads API calls, reports, settings, and live mutations belong in
  `google/`.
- Pinterest-specific integrations and operations belong in `pinterest/`.
- Logic intentionally reused across advertising platforms belongs in a
  purpose-specific top-level folder such as `audiences/`.
- Cross-channel demand and business analysis belongs in `business-trends/`.
- The repository root is reserved for shared dependencies and repository-wide
  documentation. Do not add a root `scripts/` folder unless a script genuinely
  coordinates multiple channels.

## Structure

```text
sr-ads/
  google/
    scripts/          Google Ads API and management commands
    config/           Reporting definitions and operational guardrails
    data/             Raw exports and source files
    investigations/   Dated technical and performance reviews
    changes/          Dated records of live campaign and budget changes

  pinterest/
    scripts/          Pinterest API and management commands
    config/           Pinterest reporting and guardrail configuration
    investigations/   Dated setup and performance reviews
    changes/          Dated records of live changes

  audiences/
    scripts/          Cross-channel audience generation
    config/           Reusable audience workflow definitions
    runs/             Dated source, output, and aggregate run records
    investigations/   Audience strategy and measurement reviews

  business-trends/
    investigations/   Cross-channel demand and business analysis

  requirements.txt    Shared Python dependencies
```

Folders shown above may be added when their first real artifact is introduced;
empty placeholder directories are not required.

## Script Placement

Keep Google management scripts under `google/scripts/` and Pinterest management
scripts under `pinterest/scripts/`. Examples include performance exports,
campaign listing, budget updates, and campaign status changes.

Shared code should move out of a channel folder only when at least two channels
actually use the same workflow. Prefer a purpose-specific shared folder, such as
`audiences/`, over a generic utility directory.

If the codebase grows into a larger application, reusable implementation code
can move into an importable package such as `src/sr_ads/google/`, while the
channel `scripts/` directories remain thin command-line entry points.

## Live-Change Safety

- Default new API tooling to read-only behavior.
- Separate reporting commands from commands that mutate live accounts.
- Put platform-specific limits, allowed resources, and approval requirements in
  the channel's `config/guardrails.yaml` when write operations are introduced.
- Require an explicit operator action before a live mutation.
- Record every live change in the channel's `changes/` folder with the date,
  reason, previous value, new value, and verification result.
- Keep credentials and customer-level sensitive artifacts outside Git.
