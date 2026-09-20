# Velocity Radar count

One file, [`.github/workflows/count.yml`](.github/workflows/count.yml), that adds up your own commits by day inside your own GitHub account. Instructions: <https://velocity.id8.one/guide/github>

**Status: preview.** The count runs and shows you your totals in your own run. It sends nothing anywhere.

## What it asks GitHub for

For each commit **you** authored on the default branch of the repositories your token can read, five things: its id, its date, the first line of its message, the lines it added and removed, and how many parents it has.

The first line is used once, on GitHub's machine, to sort the commit into merge, automated (chores, releases, test records), micro or other. It is then dropped.

It never asks for a file, a diff, a full commit message, an issue, a pull request or anyone else's commits. It uses no outside actions and no packages: only Python as it comes on GitHub's runner.

## What comes out

Totals by day: how many commits of each kind, and the line count of each commit. No repository names, no commit ids, no message text.

Since the second release, three summaries as well, worked out inside the first job:

- **Round the clock.** The longest unbroken run of clock hours that each hold a commit, the longest stretch with no break longer than two hours between commits, and on how many days a commit landed in 8, 12, 16, 20 or all 24 hours. Each for substantive commits and for commits of any kind.
- **Day, evening, overnight.** Only if you give your time zone in your own file, because GitHub reports commit times in UTC: the share of substantive commits from 07:00 to 18:00, 18:00 to 23:00 and 23:00 to 07:00.
- **Commit size.** The median lines of a substantive commit in all the repositories read against your public ones.

No list of commit times is handed on. The only times in the summaries are where your longest run and your longest stretch begin and end.

## How the file is laid out

The first job's code has five numbered sections, and every function says what it does in its first line:

1. **Settings.** The two classifier patterns, copied from Velocity Radar's locked formulas, and the few numbers the rest uses.
2. **Reading from GitHub.** The two queries, written out in full, and the functions that send them. This is the only place the token is used and the only place anything is asked of GitHub.
3. **Adding up.** Totals by day, the table for the last 30, 90, 180 and 365 days, the longest run and stretch, the hours of the day.
4. **Showing you the result.** The page you see is drawn straight from the totals, so it cannot show something the totals do not hold.
5. **The run.** One function that calls the others in order.

## Why two jobs

`count` holds your read-only token and has no permission to ask GitHub for a signed run token. `witness` can ask for that signed run token and never sees your token. The signed run token is how GitHub vouches for which code ran (`job_workflow_sha`) and that it ran on GitHub's machine (`runner_environment`).

## Pin the commit, not a tag

Call this workflow by its full commit id, as the instructions show. A commit id cannot be moved; a tag can.
