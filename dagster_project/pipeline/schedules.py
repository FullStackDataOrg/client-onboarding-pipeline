from dagster import ScheduleDefinition, define_asset_job, AssetSelection

daily_refresh_job = define_asset_job(
    name="daily_refresh",
    selection=AssetSelection.all(),
)

daily_refresh = ScheduleDefinition(
    job=daily_refresh_job,
    cron_schedule="0 6 * * *",
    execution_timezone="UTC",
)
