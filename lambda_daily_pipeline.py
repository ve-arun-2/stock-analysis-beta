"""
AWS Lambda: daily stock pipeline.

Calls the deployed API in order:
  1. POST /api/v1/stocks/collect                      -> pull the latest daily bars
  2. POST /api/v1/stocks/generate_technical_indicator -> compute indicators for the day

Handler: lambda_daily_pipeline.handler
Needs the `httpx` package on the function (bundle it or add a layer).

Env vars:
  API_BASE_URL     required, e.g. https://api.example.com
  COLLECT_SOURCES  default "chartink,excel_watchlist"
  HTTP_TIMEOUT     default 600  (keep the Lambda timeout >= this)

Event overrides (optional):
  {"source_list": ["chartink"], "trading_date": "2026-09-09"}
"""

import logging
from datetime import datetime, timedelta, timezone

import httpx
import boto3

IST = timezone(timedelta(hours=5, minutes=30))
logger = logging.getLogger()
logger.setLevel(logging.INFO)

COLLECT_PATH = "/api/v1/stocks/collect"
INDICATOR_PATH = "/api/v1/stocks/generate_technical_indicator"
API_BASE_URL = "http://"
ec2 = boto3.client("ec2")

def _count(payload):
    return len(payload) if isinstance(payload, list) else None


def handler(event, context):
    event = event or {}

    sources = event.get("source_list") or "excel_watchlist,chartink"
    if isinstance(sources, str):
        sources = [s.strip() for s in sources.split(",") if s.strip()]
        
    trading_date = event.get("trading_date") or datetime.now(IST).date().isoformat()

    base_url = API_BASE_URL.rstrip("/")

    result: dict = {"ok": False}
    try:
        with httpx.Client(base_url=base_url, timeout=None) as client:
            logger.info("collect_start sources=%s", sources)
            collect = client.post(COLLECT_PATH, json={"source_list": sources})
            collect.raise_for_status()
            result["collected_count"] = _count(collect.json())
            logger.info("collect_done collected=%s", result["collected_count"])

            logger.info("generate_start trading_date=%s", trading_date)
            generate = client.post(INDICATOR_PATH, json={"trading_date": trading_date})
            generate.raise_for_status()
            result["snapshot_count"] = _count(generate.json())
            logger.info("generate_done snapshots=%s", result["snapshot_count"])

        result["ok"] = True
        return result

    except httpx.HTTPStatusError as err:
        logger.error(
            "pipeline_http_error status=%s body=%s",
            err.response.status_code,
            err.response.text[:1000],
        )
        raise
    except httpx.HTTPError as err:
        logger.error("pipeline_request_failed error=%s", err)
        raise
    finally:
        logger.info("pipeline_end base_url=%s result=%s", base_url, result)
        print("Attempting to stop EC2 instances")
        instance_ids = [
            "i-0f1b99fd8d76b2621"
        ]

        ec2.stop_instances(
            InstanceIds=instance_ids
        )


if __name__ == "__main__":
    import json

    print(json.dumps(handler({}, None), indent=2))
