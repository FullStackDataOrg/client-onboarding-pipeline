"""
Source freshness sensor (stretch goal).

Runs `dbt source freshness` every hour. If any source is stale (past its SLA
defined in _sources.yml), it triggers a full daily_refresh_job run to reload
raw data and rebuild the warehouse.
"""

from dagster import sensor, SensorEvaluationContext, RunRequest, SkipReason
from dagster_dbt import DbtCliResource
from pipeline.schedules import daily_refresh_job


@sensor(job=daily_refresh_job, minimum_interval_seconds=3600)
def source_freshness_sensor(context: SensorEvaluationContext, dbt: DbtCliResource):
    """Trigger a pipeline run when dbt detects a stale source."""
    invocation = dbt.cli(["source", "freshness"], raise_on_error=False)
    result = invocation.wait()

    if not result.is_successful():
        run_key = f"freshness_alert_{context.cursor or 0}"
        context.update_cursor(str(int(context.cursor or 0) + 1))
        yield RunRequest(
            run_key=run_key,
            tags={"triggered_by": "source_freshness_sensor"},
        )
    else:
        yield SkipReason("All sources are within their freshness SLA.")
