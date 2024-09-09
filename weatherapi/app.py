import datetime
import logging
from os import environ
from typing import Annotated, List, Optional

import python_weather
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.security import APIKeyHeader
from pydantic import BaseModel

from . import __version__

__all__ = ["app"]

logging.basicConfig(level=logging.INFO)

host = environ.get("DOMAIN", "localhost")
port = 8000
protocol = "http" if host == "localhost" else "https"
base_url = (
    f"{protocol}://{host}:{port}" if host == "localhost" else f"{protocol}://{host}"
)

app = FastAPI(
    servers=[{"url": base_url, "description": "Weather app server"}],
    version=__version__,
    title="WeatherAPI",
)

API_KEY = "secure weather key"  # pragma: allowlist secret
header_scheme = APIKeyHeader(name="x-key")


class HourlyForecast(BaseModel):
    forecast_time: datetime.time
    temperature: int
    description: str


class DailyForecast(BaseModel):
    forecast_date: datetime.date
    temperature: int
    hourly_forecasts: Optional[List[HourlyForecast]] = None


class Weather(BaseModel):
    city: str
    temperature: int
    daily_forecasts: List[DailyForecast]


async def get_weather(city: str, include_hourly: bool = False) -> Weather:
    async with python_weather.Client(unit=python_weather.METRIC) as client:
        # fetch a weather forecast from a city
        weather = await client.get(city)

        daily_forecasts = []
        # get the weather forecast for a few days
        for daily in weather.daily_forecasts:
            hourly_forecasts = (
                [
                    HourlyForecast(
                        forecast_time=hourly.time,
                        temperature=hourly.temperature,
                        description=hourly.description,
                    )
                    for hourly in daily.hourly_forecasts
                ]
                if include_hourly
                else None
            )
            daily_forecasts.append(
                DailyForecast(
                    forecast_date=daily.date,
                    temperature=daily.temperature,
                    hourly_forecasts=hourly_forecasts,
                )
            )

        weather_response = Weather(
            city=city,
            temperature=weather.temperature,
            daily_forecasts=daily_forecasts,
            hourly_forecasts=hourly_forecasts,
        )
    return weather_response


@app.get("/daily", description="Get daily weather forecast for a given city")
async def get_daily_weather(
    city: Annotated[str, Query(description="city for which forecast is requested")],
) -> Weather:
    return await get_weather(city, include_hourly=False)


@app.get("/hourly", description="Get hourly weather forecast for a given city")
async def get_hourly_weather(
    city: Annotated[str, Query(description="city for which forecast is requested")],
    key: str = Depends(header_scheme),
) -> Weather:
    if key != API_KEY:
        raise HTTPException(status_code=403, detail=f"Invalid API Key; Try '{API_KEY}'")
    return await get_weather(city, include_hourly=True)
