# Velocity Radar count

One file, [`.github/workflows/count.yml`](.github/workflows/count.yml), that adds up your own commits by day inside your own GitHub account and works out your figures there. Instructions: <https://velocity.id8.one/guide/github>

**Status: preview.** The count runs and shows you your figures in your own run. It sends nothing anywhere. If you press Check my run on the guide, Velocity Radar reads the run's log back from GitHub.

## What it asks GitHub for

- **Your repositories**, each by GitHub's own id number and whether it is private. Never a repository's name: since the fifth release, a repository is read by its id.
- **Your commits.** For each commit **you** authored on the default branch of the repositories your token can read, five things: its id, its date, the first line of its message, the lines it added and removed, and how many parents it has.
- **Your contribution calendar**: how many contributions GitHub counts for you on each day, as your own token reads it.

The first line of a message is used once, on GitHub's machine, to sort the commit into merge, automated (chores, releases, test records), micro or substantive. It is then dropped.

It never asks for a file, a diff, a full commit message, an issue, a pull request or anyone else's commits. It uses no outside actions and no packages: only Python as it comes on GitHub's runner.

## The formulas run in your account

Velocity Radar's formulas are one file, [`measures.py`](measures.py). Since the fifth release the count carries it, byte for byte, with the golden cases that pin it, and works out every figure with it on GitHub's machine:

1. Job 1 writes `measures.py` and `golden.json` out of `count.yml` and checks the sha256 of each **before anything in them runs**. A file that differs stops the run.
2. It runs every golden case with GitHub's Python and stops if any gives another answer.
3. Only then does it read from GitHub and count.

The run prints which formulas ran, for example `method version 7 · measures.py sha256 dd00dae0… · 82 of 82 golden cases passed`. The `measures.py` beside this README is the same file: `sha256sum measures.py` prints the same hash.

| release | method version | measures.py sha256 |
|---|---|---|
| 7 | 7 | `dd00dae0fc187c2c71394b6f23705ee63a26a04b5ddcd87e8abbcc007bc10c9f` (no figure changes: no names in measures.py or the golden cases, and two comments in count.yml) |
| 6 | 6 | `e3c5d30838954f7f5fd6a5df4c3868be5bd02b297f21f956ee46892ce8238aed` |
| 5 | 5 | `bd8bd1f71e4c0bd1fca8582979ce592cd857ccb53aad968c4a72585f0fd3bd65` (built, never published: release 6 came first) |
| 1 to 4 | — | the count did its own arithmetic; only the two classifier patterns were copied from measures.py |

## What comes out

Everything below is worked out inside job 1 by `measures.py` and handed to job 2, which shows it in its log:

- **Substantive commits per active day** over the last 180, 90 and 30 days: the substantive commits dated inside each range, over the days your calendar shows any contribution.
- **Stretches of 30 active days**, up to eight, each with its substantive commits per active day and the median lines per substantive commit.
- **A table for the last 30, 90, 180 and 365 days**: commits of each kind, and the median lines of a substantive commit in all the repositories read and in the public ones.
- **Round the clock.** The longest unbroken run of clock hours that each hold a commit (shown from its first commit to its last since method version 6), the longest stretch with no break longer than three hours between commits (two before method version 6), and on how many days a commit landed in 8, 12, 16, 20 or all 24 hours. Each for substantive commits and for commits of any kind.
- **Day, evening, overnight.** Only if you give your time zone in your own file, because GitHub reports commit times in UTC: the share of substantive commits from 07:00 to 18:00, 18:00 to 23:00 and 23:00 to 07:00.

With them, the inputs anyone can work the figures out again from: your contribution calendar for the 730 days read, and totals by day (how many commits of each kind, and the line count of each substantive commit, all of them and the public ones).

No repository names or ids, no commit ids, no message text. No list of commit times is handed on: the only times are where your longest run and your longest stretch begin and end.

## How the file is laid out

Job 1 first writes out `measures.py` and `golden.json`. Its program then has six numbered sections, and every function says what it does in its first line:

1. **Settings.** The two files' sha256 and the few numbers the rest uses.
2. **The formulas, checked before they are used.** The hashes, then the golden cases.
3. **Reading from GitHub.** The three queries, written out in full, and the functions that send them. This is the only place the token is used and the only place anything is asked of GitHub.
4. **Your time zone.** Its offset from UTC and every change in it over the year, so that `measures.py`, which reads no files, can show times in your zone.
5. **Showing you the result.** The page you see is drawn straight from the totals, so it cannot show something the totals do not hold.
6. **The run.** One function that calls the others in order.

## Why two jobs

`count` holds your read-only token and has no permission to ask GitHub for a signed run token. `witness` can ask for that signed run token and never sees your token. The signed run token is how GitHub vouches for which code ran (`job_workflow_sha`) and that it ran on GitHub's machine (`runner_environment`).

## Pin the commit, not a tag

Call this workflow by its full commit id, as the instructions show. A commit id cannot be moved; a tag can.
