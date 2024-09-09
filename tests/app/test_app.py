import datetime

import pytest
from fastapi.testclient import TestClient

from weatherapi import __version__ as version
from weatherapi.app import HourlyForecast, app, get_weather

client = TestClient(app)


class TestRoutes:
    @pytest.mark.asyncio
    async def test_get_weather(self) -> None:
        city = "Chennai"
        weather = await get_weather(city)
        assert weather.city == city
        assert weather.temperature > 0

        assert len(weather.daily_forecasts) > 0
        daily_forecast = weather.daily_forecasts
        assert isinstance(daily_forecast, list)
        first_daily_forecast = daily_forecast[0]
        assert first_daily_forecast.forecast_date == datetime.date.today()
        assert first_daily_forecast.temperature > 0
        assert len(first_daily_forecast.hourly_forecasts) > 0

        first_hourly_forecast = first_daily_forecast.hourly_forecasts[0]
        assert isinstance(first_hourly_forecast, HourlyForecast)
        assert first_hourly_forecast.forecast_time is not None
        assert first_hourly_forecast.temperature > 0
        assert first_hourly_forecast.description is not None

    def test_weather_route(self) -> None:
        response = client.get("/?city=Chennai")
        assert response.status_code == 200
        resp_json = response.json()
        assert resp_json.get("city") == "Chennai"
        assert resp_json.get("temperature") > 0

        assert len(resp_json.get("daily_forecasts")) > 0
        daily_forecasts = resp_json.get("daily_forecasts")
        assert isinstance(daily_forecasts, list)

        first_daily_forecast = daily_forecasts[0]
        assert (
            first_daily_forecast.get("forecast_date")
            == datetime.date.today().isoformat()
        )
        assert first_daily_forecast.get("temperature") > 0
        assert len(first_daily_forecast.get("hourly_forecasts")) > 0

        first_hourly_forecast = first_daily_forecast.get("hourly_forecasts")[0]
        assert isinstance(first_hourly_forecast, dict)
        assert first_hourly_forecast.get("forecast_time") is not None
        assert first_hourly_forecast.get("temperature") > 0  # type: ignore
        assert first_hourly_forecast.get("description") is not None

    def test_openapi(self) -> None:
        expected = {
            "openapi": "3.1.0",
            "info": {"title": "WeatherAPI", "version": version},
            "servers": [
                {"url": "http://localhost:8000", "description": "Weather app server"}
            ],
            "paths": {
                "/": {
                    "get": {
                        "summary": "Get Weather Route",
                        "description": "Get weather forecast for a given city",
                        "operationId": "get_weather_route__get",
                        "parameters": [
                            {
                                "name": "city",
                                "in": "query",
                                "required": True,
                                "schema": {
                                    "type": "string",
                                    "description": "city for which forecast is requested",
                                    "title": "City",
                                },
                                "description": "city for which forecast is requested",
                            }
                        ],
                        "responses": {
                            "200": {
                                "description": "Successful Response",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/Weather"
                                        }
                                    }
                                },
                            },
                            "422": {
                                "description": "Validation Error",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/HTTPValidationError"
                                        }
                                    }
                                },
                            },
                        },
                    }
                }
            },
            "components": {
                "schemas": {
                    "DailyForecast": {
                        "properties": {
                            "forecast_date": {
                                "type": "string",
                                "format": "date",
                                "title": "Forecast Date",
                            },
                            "temperature": {"type": "integer", "title": "Temperature"},
                            "hourly_forecasts": {
                                "items": {
                                    "$ref": "#/components/schemas/HourlyForecast"
                                },
                                "type": "array",
                                "title": "Hourly Forecasts",
                            },
                        },
                        "type": "object",
                        "required": [
                            "forecast_date",
                            "temperature",
                            "hourly_forecasts",
                        ],
                        "title": "DailyForecast",
                    },
                    "HTTPValidationError": {
                        "properties": {
                            "detail": {
                                "items": {
                                    "$ref": "#/components/schemas/ValidationError"
                                },
                                "type": "array",
                                "title": "Detail",
                            }
                        },
                        "type": "object",
                        "title": "HTTPValidationError",
                    },
                    "HourlyForecast": {
                        "properties": {
                            "forecast_time": {
                                "type": "string",
                                "format": "time",
                                "title": "Forecast Time",
                            },
                            "temperature": {"type": "integer", "title": "Temperature"},
                            "description": {"type": "string", "title": "Description"},
                        },
                        "type": "object",
                        "required": ["forecast_time", "temperature", "description"],
                        "title": "HourlyForecast",
                    },
                    "ValidationError": {
                        "properties": {
                            "loc": {
                                "items": {
                                    "anyOf": [{"type": "string"}, {"type": "integer"}]
                                },
                                "type": "array",
                                "title": "Location",
                            },
                            "msg": {"type": "string", "title": "Message"},
                            "type": {"type": "string", "title": "Error Type"},
                        },
                        "type": "object",
                        "required": ["loc", "msg", "type"],
                        "title": "ValidationError",
                    },
                    "Weather": {
                        "properties": {
                            "city": {"type": "string", "title": "City"},
                            "temperature": {"type": "integer", "title": "Temperature"},
                            "daily_forecasts": {
                                "items": {"$ref": "#/components/schemas/DailyForecast"},
                                "type": "array",
                                "title": "Daily Forecasts",
                            },
                        },
                        "type": "object",
                        "required": ["city", "temperature", "daily_forecasts"],
                        "title": "Weather",
                    },
                }
            },
        }
        response = client.get("/openapi.json")
        assert response.status_code == 200
        resp_json = response.json()
        # print(resp_json)
        assert resp_json == expected
