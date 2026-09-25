#!/usr/bin/env python3
"""Velocity Radar — every published figure, defined once.

RULES FOR THIS FILE
  * Pure functions only: no file access, no network, no clock. Whoever calls a function passes every input,
    including the date a window is anchored to.
  * Every window is a span of calendar days, inclusive at both ends, in UTC.
  * Rounding is part of the definition and is written out in each function.
  * This file is hashed into measures.lock. nightly.sh runs method/lock.py verify before anything else and stops
    when the hash does not match; a deploy by hand has no such gate of its own, so the handoff's steps begin with
    the same command. Rewriting measures.lock is the act the owner approves. Raise METHOD_VERSION with every
    change to a formula and record the reason in method/METHOD_CHANGELOG.md.
  * Until the pipeline imports this file, method/check.py --pipeline is what ties the two together: it recomputes
    what the pipeline wrote and fails when they differ, and nightly.sh runs it before it builds or deploys.

One version names one measures.py: any change to what a function returns raises METHOD_VERSION, whether or not a
published number moves, and method/lock.py propose refuses a changed file whose version was not raised.

Versions 1 and 2 were a codification, not a change to anything published: each function reproduces, to the last
decimal, what the pipeline computed before this file existed (the source of each is named in its docstring), so
that the checks can prove nothing moved. Version 2 made four edge inputs match the pipeline exactly.

Version 3 is the first change to a published number. The Compare view and the substantive momentum strip stop
multiplying a stretch of days by shares measured over the year: see section 4. bundle.py imports the section 4
functions and stores their results; the browser reads them and multiplies nothing. The defects still kept are
listed in method/METHOD_CHANGELOG.md.

Version 4 uses a measurable public commit share for an approximate record instead of borrowing that share, and
adds the median size of substantive commits to each counted momentum stretch. See the changelog for the effect.

Version 5 changes no figure. It moves into this file, unchanged, the arithmetic the public count (count.yml, release 4)
and bundle.py's momentum() did for themselves, so that the count can carry this file byte for byte into a person's own
GitHub account and work out every Detailed stats figure there: section 7.

Version 6 changes two figures in section 7, both the owner's decisions of 23 September 2026. A stretch now ends at a
break longer than three hours, not two (LONGEST_BREAK). The run keeps its count of clock hours but is also measured
from its first commit to its last, as the stretch is, so that the two read on the same scale and the stretch, which
allows the longer break, is never the shorter figure. Each stretch also says which break it allowed.

Version 7 changes no figure and no function. This file and method/golden.json are published in the count's public
repository, so they no longer name the people whose public figures some golden cases were taken from: a comment here
and the notes of seven cases say "person A" to "person E" instead. Their arguments and outputs are unchanged.
"""
import collections
import datetime as dt
import re
import statistics
import statistics as st

METHOD_VERSION = 7

# ---------------------------------------------------------------------------------------------------------------
# 1. Rates over a window                                                     source: windows.py rate()
# ---------------------------------------------------------------------------------------------------------------

def window_rates(public_commits, private_contributions, active_days):
    """Public = public commits / active days. All work = (public commits + private contributions) / active days.
    An active day is a day the contribution calendar shows at least one contribution. One decimal."""
    if not active_days:
        return dict(public=0, all=0)
    return dict(public=round(public_commits / active_days, 1),
                all=round((public_commits + private_contributions) / active_days, 1))


# ---------------------------------------------------------------------------------------------------------------
# 2. Which commits are substantive                                            source: substantive_rules.py
# ---------------------------------------------------------------------------------------------------------------

AUTO = re.compile(r"^(chore|build|ci|release|bump|deploy|sync|publish|version|merge|revert|update (readme|deps|dependencies|changelog|lock)|\[?bot\]?|auto|evidence|logs?[:/]|test-?runs?|record(ed)? (run|evidence)|apply (formatting|prettier|fmt)|regenerat|prepare release|v?\d+\.\d+\.\d+)", re.I)
MICRO = re.compile(r"^(wip|x+|\.+|fix|update|tweak|tmp|test|stuff|more|misc|changes?|save)$", re.I)


def commit_kind(is_merge, subject):
    """merge, automation, micro or substantive, decided from the parent count and the subject line alone.
    Size and content play no part."""
    s = (subject or "").strip()
    if is_merge:
        return "merge"
    if AUTO.search(s):
        return "automation"
    if len(s) <= 3 or MICRO.match(s):
        return "micro"
    return "substantive"


def substantive_rate(public_rate, substantive_share):
    """Substantive commits a day, public work only = public rate x substantive share. One decimal.
    source: bundle.py, velocity["substantive"]

    KNOWN DEFECT (kept through version 4): the pipeline passes the UNROUNDED sample share here but publishes the
    share rounded to three decimals, so for 14 of 468 people on 18 Sep 2026 the two published numbers do not
    multiply to the published result (one of them: 232.0 x 0.839 = 194.6, published 194.5)."""
    return round(public_rate * substantive_share, 1)


# ---------------------------------------------------------------------------------------------------------------
# 3. The estimate with private work included, over 365 days                   source: bundle.py velocity["estimate"]
# ---------------------------------------------------------------------------------------------------------------

MIN_PUBLIC_CONTRIBUTIONS_TO_MEASURE = 30
COMMIT_SHARE_SOURCES = dict(
    own="counted by SHA in their own repositories, private included",
    public="public commits as a share of public contributions",
    typical="too little public work to measure it, so the list's median",
    approximate="the list's median, too little public work to measure either share")


def estimate(*, substantive_share, margin, public_commits, private_contributions, active_days, calendar_total,
             own_repo_commits, own_repos_read, typical_commit_share, own_repo_substantive=None):
    """Two steps. The private count becomes commits through the commit share; commits become substantive commits
    through the substantive share.

    The commit share, in order of preference:
      own      the person's own repositories were read, private included: commits counted by SHA / contributions
      public   public commits / public contributions, when there are at least 30 public contributions
      typical  otherwise the list's median
    own_repos_read says whether an own-repository read exists at all; one that counted no commits in the year falls
    through to the public or typical share, and the result still says private work was measured, as the pipeline does.
    Assumes private work has the same commit share and the same substantive share as public work.

    Since version 3: commits = public commits + commit share x private contributions, for the public and the typical
    share alike. Public commits are counted by GitHub, so no share is applied to them. For the public share this is
    the same number as before (share x all contributions); for the typical share it is not, because a borrowed share
    used to be applied to public contributions whose commits are known. And when own_repo_substantive is given (the
    substantive commits counted in the person's own repositories over the year) it IS the total: no share is applied."""
    total = calendar_total or (public_commits + private_contributions)
    public_contributions = max(total - private_contributions, 0)
    if own_repo_commits:
        commits = own_repo_commits
        f = min(1.0, commits / total) if total else 1.0
        src = COMMIT_SHARE_SOURCES["own"]
    elif public_contributions >= MIN_PUBLIC_CONTRIBUTIONS_TO_MEASURE:
        f = min(1.0, public_commits / public_contributions)
        commits = public_commits + f * private_contributions
        src = COMMIT_SHARE_SOURCES["public"]
    else:
        f = typical_commit_share
        commits = public_commits + f * private_contributions
        src = COMMIT_SHARE_SOURCES["typical"]
    counted = own_repo_commits and own_repo_substantive is not None
    est = own_repo_substantive if counted else substantive_share * commits
    return dict(share=substantive_share, commit_share=round(f, 3), commit_share_source=src,
                factor=round(substantive_share * f, 4), contributions=total, commits=round(commits),
                public_commits=public_commits, substantive_public=round(public_commits * substantive_share),
                private=private_contributions, total=round(est),
                per_day=round(est / active_days, 1) if active_days else None,
                per_day_moe=round(margin * commits / active_days, 1) if (margin is not None and active_days) else None,
                active_days=active_days, private_shared=private_contributions > 0,
                private_measured=bool(own_repos_read))


def estimate_approximate(*, public_commits, private_contributions, active_days, calendar_total,
                         typical_commit_share, typical_substantive_share):
    """For someone whose public commits have not been sampled: the substantive share is borrowed from the list's
    median, so the record stays approximate. The commit share is measured as public commits / public contributions
    when there are at least 30 public contributions, with a cap at 1; below that it is also borrowed from the list.
    Applies only when calendar_total >= 365 and there are active days; otherwise there is no estimate and this
    returns None. Commits = public commits + commit share x private contributions."""
    if not (calendar_total >= 365 and active_days):
        return None
    public_contributions = max(calendar_total - private_contributions, 0)
    if public_contributions >= MIN_PUBLIC_CONTRIBUTIONS_TO_MEASURE:
        f = min(1.0, public_commits / public_contributions)
        source = COMMIT_SHARE_SOURCES["public"]
    else:
        f = typical_commit_share
        source = COMMIT_SHARE_SOURCES["approximate"]
    share = typical_substantive_share
    commits = public_commits + f * private_contributions
    est = share * commits
    return dict(share=share, commit_share=round(f, 3), commit_share_source=source,
                factor=round(share * f, 4), approximate=True, contributions=calendar_total, commits=round(commits),
                public_commits=public_commits, substantive_public=None, private=private_contributions,
                total=round(est), per_day=round(est / active_days, 1), per_day_moe=None, active_days=active_days,
                private_shared=private_contributions > 0, private_measured=False)


# ---------------------------------------------------------------------------------------------------------------
# 4. The estimate over a stretch of days shorter than the year      new in version 3; bundle.py imports these
# ---------------------------------------------------------------------------------------------------------------

WINDOW_SPANS = (30, 90, 180)          # days. 365 days is the year's estimate itself (section 3), not a second figure;
                                      # only someone with no year record has the 365-day window put through window_estimate
MAX_CENSUS_LAG_DAYS = 3               # a count that stops more than this many days before the window ends is not used


def window_bounds(end_day, span):
    """First and last day of a window of span calendar days ending on end_day, both inclusive, as ISO strings."""
    import datetime as dt
    end = dt.date.fromisoformat(end_day)
    return (end - dt.timedelta(days=span - 1)).isoformat(), end.isoformat()


def sum_in_window(per_day, start_day, end_day):
    """Sum of a {iso_day: count} mapping over the days from start_day to end_day, inclusive."""
    return sum(v for d, v in (per_day or {}).items() if start_day <= d <= end_day)


def active_in_window(calendar, start_day, end_day):
    """Active days: the days from start_day to end_day, inclusive, on which the contribution calendar shows at
    least one contribution. calendar is {iso_day: contributions}."""
    return sum(1 for d, v in (calendar or {}).items() if start_day <= d <= end_day and v > 0)


def counted_window_end(anchor_day, census_through_day):
    """The last day of the window that can be COUNTED for a person whose own repositories were read.

    anchor_day is the last day of the window everyone else is measured over. census_through_day is the last
    complete UTC day the read of their repositories covers. The counted window ends on the earlier of the two, so
    a day the read has not seen is never counted as empty. When the read stops more than MAX_CENSUS_LAG_DAYS before
    the anchor there is no counted window (None) and the person is estimated like everyone else."""
    import datetime as dt
    if not anchor_day or not census_through_day:
        return None
    end = min(anchor_day, census_through_day)
    lag = (dt.date.fromisoformat(anchor_day) - dt.date.fromisoformat(end)).days
    return end if lag <= MAX_CENSUS_LAG_DAYS else None


def window_estimate(*, substantive_share, commit_share, public_commits, private_contributions, active_days,
                    counted_substantive=None, counted_active_days=None):
    """Substantive commits a day over one window of days, private work included. One decimal.

    counted    (counted_substantive is given) the person's own repositories were read, private included, so the
               substantive commits dated inside the window are counted one by one and divided by the active days
               of the same window. No share is applied to anything.
    estimated  everyone else. GitHub counts, for the window itself, the person's public commits and their private
               contributions, but not what kind the private ones are. So:
                   commits     = public commits + commit share x private contributions
                   substantive = commits x substantive share
               divided by the window's active days. Public commits are already commits, so the commit share is
               applied to the private count only. Both shares are the PUBLISHED 365-day shares, as rounded on the
               person's record, and the figure is the published (rounded) count over the published days.

    KNOWN LIMIT: an estimated window still uses the year's two shares. The sample of a person's public commits
    carries no dates, so there is no share for a shorter window; only a counted window is free of this. Measured on
    the owner for the 30 days to 18 Sep 2026: year's substantive share 0.707, the window's own 0.586."""
    if counted_substantive is not None:
        ad = counted_active_days
        return dict(basis="counted", substantive=counted_substantive, active_days=ad,
                    per_day=round(counted_substantive / ad, 1) if ad else None)
    if substantive_share is None or commit_share is None:
        return None
    sub = round(substantive_share * (public_commits + commit_share * private_contributions))
    return dict(basis="estimated", substantive=sub, active_days=active_days,       # the figure is the PUBLISHED count over
                per_day=round(sub / active_days, 1) if active_days else None)      # the published days, so a reader can redo it


def census_covers(start_day, end_day, census_since_day, census_read_day):
    """Whether a read of someone's own repositories covers every day from start_day to end_day: it began on or
    before start_day and was made on or after end_day. A day still in progress when the read was made counts as
    covered, because the calendar it is divided by was read in the same run and is as partial as the count."""
    return bool(start_day and end_day and census_since_day and census_read_day
                and census_since_day <= start_day and end_day <= census_read_day)


def counted_stretch(per_day_substantive, calendar, start_day, end_day):
    """One stretch of the momentum strip, counted: the substantive commits dated from start_day to end_day, per
    active day of the same stretch. mean = all of them / active days; median = the median over the active days of
    each day's own count. One decimal each. Active days come from the contribution calendar, as everywhere."""
    days = [d for d, v in (calendar or {}).items() if start_day <= d <= end_day and v > 0]
    if not days:
        return None
    total = sum_in_window(per_day_substantive, start_day, end_day)
    return dict(substantive=total, active_days=len(days), mean=round(total / len(days), 1),
                median=round(st.median([(per_day_substantive or {}).get(d, 0) for d in days]), 1))


def commit_size_stretch(dated_sizes, start_day, end_day):
    """Median lines changed per substantive commit dated from start_day to end_day, both inclusive. dated_sizes is
    [[iso_day, additions + deletions], ...] after merges, automation and micro commits have been removed. The commit
    count is the number whose size GitHub reported. One decimal; an empty covered stretch has no median."""
    sizes = [lines for day, lines in (dated_sizes or []) if start_day <= day <= end_day]
    return dict(median_lines=round(st.median(sizes), 1) if sizes else None, commits=len(sizes))


def momentum_baseline(means):
    """The strip's baseline: the mean of the third to fifth newest stretches (all from the third on when there are
    fewer than five), never under 0.5. means is newest first. One decimal. None with fewer than three stretches.
                                                                                        source: bundle.py momentum()"""
    if len(means) < 3:
        return None
    return round(max(st.mean(means[2:5] if len(means) >= 5 else means[2:]), 0.5), 1)


def compare_value(measure, *, window_all_rate=None, factor=None, share=None, substantive=None):
    """What the Compare view draws when it still has to multiply.    source: page_template.html cmpValue()

    'all'  the span's all-work rate, as stored.
    'sub'  the 365-day public substantive rate; the page offers it at 365 days only.
    'est'  ONLY for the busiest-day spans (a person's busiest 25, 50 or 100 days): mean contributions on those
           days x the 365-day factor. For the 30, 90 and 180-day windows the page reads what window_estimate()
           stored, and at 365 days the year's estimate (section 3); it multiplies nothing for those.

    Until version 3 'est' was also used for the windows, as the window's all-work rate x the 365-day factor. That
    was wrong twice: the factor's commit share was applied to public commits, which are already commits (so the
    365-day Compare figure disagreed with the person's own 365-day estimate), and the year's shares were applied
    to a shorter window. Shown for the owner at 30 days, 19 Sep 2026: 68.6, against 57.1 counted.

    KNOWN LIMIT: the busiest-day spans still use the year's factor; nobody's commits are dated by the calendar's
    own days closely enough to count them on single days."""
    if measure == "sub":
        return substantive
    if window_all_rate is None:
        return None
    if measure == "all":
        return window_all_rate
    f = factor if factor is not None else share      # cmpShare(): a record written before the factor existed carries only the share
    return None if f is None else window_all_rate * f


# ---------------------------------------------------------------------------------------------------------------
# 5. The graph image's retired second figure
# ---------------------------------------------------------------------------------------------------------------

def banner_commits_per_active_day(public_commits, private_contributions, active_days):
    """The second figure on the graph image: (public commits + private contributions) / active days, labelled
    'commits per active day, private included'.                                       source: vc-portal/api/graph.js

    RETIRED 19 Sep 2026: the graph no longer draws this figure (it counted every private pull request, review and
    issue as a commit). Kept so the frozen golden cases for it still run; nothing published calls it."""
    return (public_commits + private_contributions) / active_days if active_days else 0


# ---------------------------------------------------------------------------------------------------------------
# 6. Commit size                                       source: commit_size.py size_stats(), build_research.py
# ---------------------------------------------------------------------------------------------------------------

def percentile(values, p):
    """Linear interpolation between closest ranks (the numpy default)."""
    if not values:
        return None
    xs = sorted(values)
    k = (len(xs) - 1) * p
    f = int(k)
    c = min(f + 1, len(xs) - 1)
    return xs[f] + (xs[c] - xs[f]) * (k - f)


MIN_COMMITS_FOR_SIZE_STATS = 10


def size_stats(sizes, active_days, year_commits=None):
    """Lines changed per non-merge commit. None under 10 commits. The trimmed mean drops the largest 5%.

    lines_per_active_day EXTRAPOLATES: trimmed mean of the sampled repositories x all the year's commits."""
    if len(sizes) < MIN_COMMITS_FOR_SIZE_STATS:
        return None
    s = sorted(sizes)
    cut = s[:max(1, int(len(s) * 0.95))]
    trimmed = st.mean(cut)
    return dict(n=len(sizes), median=round(st.median(s), 1), p25=round(percentile(s, .25), 1),
                p75=round(percentile(s, .75), 1), p90=round(percentile(s, .9), 1),
                share_ge200=round(sum(1 for x in s if x >= 200) / len(s), 3),
                share_le10=round(sum(1 for x in s if x <= 10) / len(s), 3),
                trimmed_mean=round(trimmed, 1),
                lines_per_active_day=(round(trimmed * year_commits / active_days, 0) if (active_days and year_commits) else None))


SPANS = (30, 90, 180, 365)


def size_median_by_span(dated, anchor_day):
    """Median lines a commit for each span ending on anchor_day (an ISO date string). dated is a list of
    [iso_day, lines]. A span with fewer than 10 commits gives None, and the page falls back to the year's figure.

    KNOWN DEFECT (kept through version 4): the lower bound is anchor - n days, so a span covers n + 1 days, one more
    than the rate windows, which cover n. And nothing caps the upper end at anchor_day."""
    import datetime as dt
    if not dated:
        return None
    end = dt.date.fromisoformat(anchor_day)
    out = {}
    for n in SPANS:
        cut = (end - dt.timedelta(days=n)).isoformat()
        xs = [v for d, v in dated if d >= cut]
        out[str(n)] = round(st.median(xs), 1) if len(xs) >= MIN_COMMITS_FOR_SIZE_STATS else None
    return out


# ---------------------------------------------------------------------------------------------------------------
# 7. Counted in the person's own run          new in version 5; source: count.yml release 4 (5fb881d), bundle.py momentum()
# ---------------------------------------------------------------------------------------------------------------
# The public count (velocity-radar/count) carries this file byte for byte into the person's own GitHub account and
# works out every Detailed stats figure with it there. The settings and the functions from median_lines to momentum are
# moved here unchanged, character for character, from the release-4 count and from bundle.py; golden cases whose
# expected outputs were produced by those two programs, not by this file, prove it. The functions after them only take
# the count's plain data (lists, dates as text) in and hand plain data out, so that golden cases can call them, and
# are what the count and the nightly re-check call: commit_days(), counted_figures() and rhythm_figures().

KINDS = ("substantive", "merge", "automated", "micro")
WINDOWS = (30, 90, 180, 365)              # the table covers these many days
LONGEST_BREAK = dt.timedelta(hours=3)     # a stretch ends when no commit lands for longer than this (2 h until version 6)
OVERNIGHT = (23, 0, 1, 2, 3, 4, 5, 6)
BANDS = {"day, 07:00 to 18:00": range(7, 18), "evening, 18:00 to 23:00": range(18, 23),
         "overnight, 23:00 to 07:00": OVERNIGHT}
HOUR = dt.timedelta(hours=1)
Commit = collections.namedtuple("Commit", "day kind lines when private")
COUNT_KINDS = {"automation": "automated"}     # commit_kind() says automation; the count's column is automated


def median_lines(commits):
    """The size in lines of the middle commit, or None with fewer than ten commits to go on."""
    lines = [c.lines for c in commits if c.lines is not None]
    return round(statistics.median(lines)) if len(lines) >= 10 else None


def totals_by_day(commits):
    """For each day: how many commits of each kind, and the line count of each substantive commit."""
    days = collections.defaultdict(lambda: dict({k: 0 for k in KINDS}, lines=[]))
    for c in commits:
        days[c.day][c.kind] += 1
        if c.kind == "substantive" and c.lines is not None:
            days[c.day]["lines"].append(c.lines)
    return {day: dict(total, lines=sorted(total["lines"])) for day, total in sorted(days.items())}


def window_table(commits, through):
    """One row for each of the last 30, 90, 180 and 365 days, with commit size in all repositories and public ones."""
    rows = []
    for span in WINDOWS:
        first_day = (through - dt.timedelta(days=span - 1)).isoformat()
        inside = [c for c in commits if c.day >= first_day]
        substantive = [c for c in inside if c.kind == "substantive"]
        public = [c for c in substantive if not c.private]
        rows.append({"days": span, "commits": len(inside), **{k: sum(c.kind == k for c in inside) for k in KINDS},
                     "median_lines": median_lines(substantive), "public_substantive": len(public),
                     "median_lines_public_only": median_lines(public)})
    return rows


def longest_chain(times, longest_gap):
    """The first and last of the longest chain of times in which no gap between neighbours exceeds longest_gap."""
    times = sorted(times)
    best, start = (times[0], times[0]), times[0]
    for earlier, later in zip(times, times[1:] + [None]):
        if later is None or later - earlier > longest_gap:
            if earlier - start > best[1] - best[0]:
                best = (start, earlier)
            start = later
    return best


def longest_run(commits, clock):
    """The longest unbroken run of clock hours that each hold at least one commit. "hours" counts those clock hours and
    "from"/"to" bound them; "span_hours" is the time from the run's first commit to its last, "first_commit" to
    "last_commit", measured as longest_stretch() measures a stretch (version 6)."""
    per_hour = collections.Counter(c.when.replace(minute=0, second=0, microsecond=0) for c in commits)
    first, last = longest_chain(per_hour, HOUR)
    each = [per_hour[first + HOUR * i] for i in range(int((last - first) / HOUR) + 1)]
    inside = [c.when for c in commits if first <= c.when < last + HOUR]
    return {"hours": len(each), "from": clock(first).strftime("%Y-%m-%d %H:%M"),
            "to": clock(last + HOUR).strftime("%Y-%m-%d %H:%M"), "commits": sum(each), "fewest_in_an_hour": min(each),
            "median_in_an_hour": statistics.median(each), "first_hour_of_day": clock(first).hour, "per_hour": each[:120],
            "span_hours": round((max(inside) - min(inside)) / HOUR, 1),
            "first_commit": clock(min(inside)).strftime("%Y-%m-%d %H:%M"),
            "last_commit": clock(max(inside)).strftime("%Y-%m-%d %H:%M")}


def longest_stretch(commits, clock):
    """The longest stretch of commits with no break longer than LONGEST_BREAK between one and the next."""
    times = sorted(c.when for c in commits)
    first, last = longest_chain(times, LONGEST_BREAK)
    inside = [t for t in times if first <= t <= last]
    longest_break = max((later - earlier for earlier, later in zip(inside, inside[1:])), default=dt.timedelta(0))
    return {"hours": round((last - first) / HOUR, 1), "from": clock(first).strftime("%Y-%m-%d %H:%M"),
            "to": clock(last).strftime("%Y-%m-%d %H:%M"), "commits": len(inside),
            "longest_break_minutes": round(longest_break / dt.timedelta(minutes=1)),
            "break_allowed_minutes": round(LONGEST_BREAK / dt.timedelta(minutes=1))}


def hours_of_the_day(commits, clock, zone_given):
    """On how many days commits landed in many different hours; with a time zone, also the bands and the nights."""
    hours_by_day, hours_by_night = collections.defaultdict(set), collections.defaultdict(set)
    by_hour = collections.Counter()
    for c in commits:
        local = clock(c.when)
        by_hour[local.hour] += 1
        hours_by_day[local.date()].add(local.hour)
        if local.hour in OVERNIGHT:       # 23:00 opens the night of that day; 00:00 to 06:59 close the night before
            night = local.date() if local.hour == 23 else local.date() - dt.timedelta(days=1)
            hours_by_night[night].add(local.hour)
    spread = [len(hours) for hours in hours_by_day.values()]
    result = {"days": len(spread), "median_hours_a_day": statistics.median(spread),
              "days_with_at_least": {str(n): sum(s >= n for s in spread) for n in (8, 12, 16, 20, 24)}}
    if zone_given:
        result["bands"] = []
        for band, hours in BANDS.items():
            share = 100 * sum(by_hour[h] for h in hours) / len(commits)
            result["bands"].append({"band": band, "commits": sum(by_hour[h] for h in hours),
                                    "percent_of_commits": round(share, 1),
                                    "percent_per_hour_of_the_band": round(share / len(hours), 2)})
        result["nights"] = {"nights_with_a_commit": len(hours_by_night),
                            "with_one_in_4_or_more_of_the_8_hours": sum(len(h) >= 4 for h in hours_by_night.values()),
                            "with_one_in_all_8_hours": sum(len(h) == 8 for h in hours_by_night.values())}
    return result


def momentum(days, N=30, K=8):
    """K non-overlapping windows of N active days, newest first; baseline = mean of windows 3-5."""
    act = sorted([(d, c) for d, c in days.items() if c > 0]); wins = []
    for k in range(K):
        hi = len(act) - N * k; lo = hi - N
        if lo < 0: break
        w = act[lo:hi]; vals = [c for _, c in w]
        span = (dt.date.fromisoformat(w[-1][0]) - dt.date.fromisoformat(w[0][0])).days + 1
        wins.append(dict(mean=round(st.mean(vals), 1), median=st.median(vals), span=span, top3=round(sum(sorted(vals)[-3:]) / sum(vals), 2) if sum(vals) else 0, start=w[0][0], end=w[-1][0]))
    if len(wins) < 3: return dict(windows=wins, status="Too sparse", base=0)
    last, prev = wins[0], wins[1]; base = max(st.mean([w["mean"] for w in (wins[2:5] if len(wins) >= 5 else wins[2:])]), 0.5)
    L, P = last["mean"] / base, prev["mean"] / base
    if L >= 2 and P >= 2: status = "Sustained"
    elif L >= 2 and (last["top3"] > 0.30 or last["median"] < 1.5 * base): status = "Spike"
    elif L >= 2 and P < 1.5 and len(wins) > 2 and wins[2]["mean"] / base >= 2: status = "Campaigns"
    elif L >= 2: status = "Emerging"
    elif L <= 0.5 and P <= 0.75: status = "Fading"
    elif L >= 1.3 and P >= 1.3: status = "Rising"
    elif L >= 1.5: status = "Ticking up"
    else: status = "Flat"
    return dict(windows=wins, status=status, base=round(base, 1))


def as_commits(rows):
    """The count's commit records from [[authored time as GitHub gives it, kind, lines or None, private], ...], with
    kind as commit_kind() names it. The day is the UTC date of the authored time.      source: count.yml read_commits()"""
    out = []
    for authored, kind, lines, private in rows:
        when = dt.datetime.fromisoformat(authored.replace("Z", "+00:00")).astimezone(dt.timezone.utc)
        out.append(Commit(when.date().isoformat(), COUNT_KINDS.get(kind, kind), lines, when, private))
    return out


def commit_days(rows, counted_through):
    """The per-day record the count hands on and the nightly re-check reads, for every day with a commit up to
    counted_through (an ISO date): the commits of each kind and the sorted line count of each substantive commit, as
    totals_by_day() gives them, then public, the substantive commits in public repositories, and public_lines, their
    sorted line counts. rows as as_commits() takes them."""
    commits = [c for c in as_commits(rows) if c.day <= counted_through]
    days, public = totals_by_day(commits), totals_by_day([c for c in commits if not c.private])
    for day, total in days.items():
        total["public"] = (public.get(day) or {}).get("substantive", 0)
        total["public_lines"] = (public.get(day) or {}).get("lines", [])
    return days


def day_commits(days):
    """The commits a commit_days() record describes, as window_table() reads them: day, kind, line count and whether
    private. The record keeps no times (when is None) and does not say which commit had which line count, only which
    counts were public; window_table() reads only counts and medians, so its result is the one the commits give.
    A record whose public_lines were left out to fit does not say which counts were public: they are then given to
    private commits first, so every count stays right and only the public-only median cannot be worked out."""
    out = []
    for day, total in sorted(days.items()):
        for kind in KINDS[1:]:
            out += [Commit(day, kind, None, None, None)] * total.get(kind, 0)
        public = total.get("public", 0)
        lines, public_lines = total.get("lines") or [], total.get("public_lines")
        if public_lines is None:
            public_lines = lines[:max(0, len(lines) - (total["substantive"] - public))]
        private_lines = sorted((collections.Counter(lines) - collections.Counter(public_lines)).elements())
        out += [Commit(day, "substantive", n, None, False) for n in public_lines]
        out += [Commit(day, "substantive", None, None, False)] * (public - len(public_lines))
        out += [Commit(day, "substantive", n, None, True) for n in private_lines]
        out += [Commit(day, "substantive", None, None, True)] * (total["substantive"] - public - len(private_lines))
    return out


def counted_figures(days, calendar, counted_through):
    """Every Detailed stats figure that can be worked out again from what the count hands on.

      days             commit_days()
      calendar         {"from": first day, "counts": [contributions on that day, the next, ...]}: the contribution
                       calendar as the person's own token reads it, from the first day the count read to counted_through
      counted_through  the last complete UTC day the count read, an ISO date

    ranges     180, 90 and 30 days to counted_through, in the order the page draws them: the substantive commits dated
               inside each, counted one by one, over the calendar's active days in it (window_estimate, counted)
    stretches  the momentum strip, oldest first: momentum() over the calendar, each stretch counted (counted_stretch)
               with its median lines per substantive commit (commit_size_stretch). None at all unless the count's read
               covers every stretch (census_covers), as in bundle.py
    windows    the run table: window_table() over the commits the days describe (day_commits)

    A days record whose line counts were left out to fit gives no median where it has none (see day_commits)."""
    first = dt.date.fromisoformat(calendar["from"])
    cal = {(first + dt.timedelta(days=i)).isoformat(): n for i, n in enumerate(calendar["counts"])}
    per_day = {day: total["substantive"] for day, total in days.items()}
    ranges = []
    for span in sorted(WINDOW_SPANS, reverse=True):
        start, end = window_bounds(counted_through, span)
        counted = window_estimate(substantive_share=None, commit_share=None, public_commits=0, private_contributions=0,
                                  active_days=0, counted_substantive=sum_in_window(per_day, start, end),
                                  counted_active_days=active_in_window(cal, start, end))
        ranges.append(dict(span=span, start=start, end=end, substantive=counted["substantive"],
                           active_days=counted["active_days"], counted=counted["per_day"]))
    wins = momentum(cal)["windows"]
    covered = [census_covers(w["start"], w["end"], calendar["from"], counted_through) for w in wins]
    subs = [counted_stretch(per_day, cal, w["start"], w["end"]) if ok else None for w, ok in zip(wins, covered)]
    dated = [[day, n] for day, total in sorted(days.items()) for n in total.get("lines") or []]
    stretches = []
    if all(subs):
        for w, sub in reversed(list(zip(wins, subs))):
            size = commit_size_stretch(dated, w["start"], w["end"])
            stretches.append(dict(start=w["start"], end=w["end"], span=w["span"], counted=sub["mean"],
                                  median_lines=size["median_lines"], sized_commits=size["commits"]))
    return dict(ranges=ranges, stretches=stretches,
                windows=window_table(day_commits(days), dt.date.fromisoformat(counted_through)))


def local_clock(to_local):
    """The clock longest_run(), longest_stretch() and hours_of_the_day() are given, from [[UTC instant, offset in
    minutes], ...] oldest first: a time is shown at the offset that holds from the latest instant at or before it (the
    first offset before the first instant). With no entries a time stays as it is, in UTC."""
    if not to_local:
        return lambda when: when
    changes = [(dt.datetime.fromisoformat(instant.replace("Z", "+00:00")), dt.timezone(dt.timedelta(minutes=minutes)))
               for instant, minutes in to_local]

    def clock(when):
        zone = changes[0][1]
        for instant, offset in changes:
            if when < instant:
                break
            zone = offset
        return when.astimezone(zone)
    return clock


def rhythm_figures(rows, counted_through, to_local, zone_given):
    """Round the clock and the hours of the day over the 365 days to counted_through, as the release-4 count's run
    worked them out: the longest run and the longest stretch of substantive commits and of commits of any kind, and
    hours_of_the_day() for the substantive ones. These cannot be worked out again later: commit times never leave the
    count.

      rows        as as_commits() takes them
      to_local    the time zone the person named, as local_clock() takes it; [] for none. The count works it out with
                  zoneinfo, which reads files and so cannot run in this file
      zone_given  whether a time zone was named: the day, evening and overnight bands need one

    Returns dict(longest=..., hours_of_the_day=...), both {} when the year holds no substantive commit."""
    commits = [c for c in as_commits(rows) if c.day <= counted_through]
    year = [c for c in commits if c.day >= (dt.date.fromisoformat(counted_through) - dt.timedelta(days=364)).isoformat()]
    substantive = [c for c in year if c.kind == "substantive"]
    if not substantive:
        return dict(longest={}, hours_of_the_day={})
    clock = local_clock(to_local)
    return dict(longest={"run_substantive": longest_run(substantive, clock), "run_any": longest_run(year, clock),
                         "stretch_substantive": longest_stretch(substantive, clock),
                         "stretch_any": longest_stretch(year, clock)},
                hours_of_the_day=hours_of_the_day(substantive, clock, zone_given))
