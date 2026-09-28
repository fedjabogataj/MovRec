#!/bin/bash
set -e

# cron jobs run with a stripped-down environment, not this container's —
# capture it now (while we still have it) so the crontab line can source it.
printenv | sed 's/^\(.*\)$/export \1/' > /code/.cron_env

exec cron -f
