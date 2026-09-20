# Velocity Radar count

One file, [`.github/workflows/count.yml`](.github/workflows/count.yml), that adds up your own commits by day inside your own GitHub account. Instructions: <https://velocity.id8.one/guide/github>

**Status: preview.** The count runs and shows you your totals in your own run. It sends nothing anywhere.

## What it asks GitHub for

For each commit **you** authored on the default branch of the repositories your token can read, five things: its id, its date, the first line of its message, the lines it added and removed, and how many parents it has.

The first line is used once, on GitHub's machine, to sort the commit into merge, automated (chores, releases, test records), micro or other. It is then dropped.

It never asks for a file, a diff, a full commit message, an issue, a pull request or anyone else's commits. It uses no outside actions and no packages: only Python as it comes on GitHub's runner.

## What comes out

Totals by day: how many commits of each kind, and the line count of each commit. No repository names, no commit ids, no message text.

## Why two jobs

`count` holds your read-only token and has no permission to ask GitHub for a signed run token. `witness` can ask for that signed run token and never sees your token. The signed run token is how GitHub vouches for which code ran (`job_workflow_sha`) and that it ran on GitHub's machine (`runner_environment`).

## Pin the commit, not a tag

Call this workflow by its full commit id, as the instructions show. A commit id cannot be moved; a tag can.
