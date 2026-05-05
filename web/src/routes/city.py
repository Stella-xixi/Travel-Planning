"""City API routes."""
from fastapi import APIRouter
from typing import List

router = APIRouter()


# Sample city data (in production, this would come from a database or config)
CITIES = [
    {"id": "beijing", "name": "北京", "region": "华北", "tags": ["历史文化", "首都", "古建筑"]},
    {"id": "shanghai", "name": "上海", "region": "华东", "tags": ["现代都市", "购物", "美食"]},
    {"id": "hangzhou", "name": "杭州", "region": "华东", "tags": ["自然风光", "人文历史", "休闲"]},
    {"id": "chengdu", "name": "成都", "region": "西南", "tags": ["美食", "休闲", "熊猫"]},
    {"id": "xian", "name": "西安", "region": "西北", "tags": ["历史文化", "古都", "美食"]},
    {"id": "xiamen", "name": "厦门", "region": "华南", "tags": ["海滨", "休闲", "文艺"]},
]


@router.get("/cities")
async def list_cities(region: str = None, tags: str = None):
    """List cities with optional filtering."""
    result = CITIES

    if region:
        result = [c for c in result if c.get("region") == region]

    if tags:
        tag_list = tags.split(",")
        result = [c for c in result if any(t in c.get("tags", []) for t in tag_list)]

    return {"cities": result}


@router.get("/cities/{city_id}")
async def get_city(city_id: str):
    """Get city details."""
    city = next((c for c in CITIES if c["id"] == city_id), None)
    if not city:
        return {"error": "City not found"}

    # Add more details
    city_details = {
        **city,
        "description": f"{city['name']}是{city['region']}的热门旅游城市，以{city['tags'][0]}著称。",
        "attractions": [
            {"name": f"{city['name']}著名景点1", "type": "景点", "duration": "3小时", "ticket": 50},
            {"name": f"{city['name']}著名景点2", "type": "景点", "duration": "4小时", "ticket": 60},
        ],
        "avg_budget_per_day": 400,
        "best_seasons": ["春季", "秋季"],
    }

    return city_details


@router.get("/cities/{city_id}/attractions")
async def get_city_attractions(city_id: str):
    """Get city attractions."""
    city = next((c for c in CITIES if c["id"] == city_id), None)
    if not city:
        return {"error": "City not found"}

    return {
        "city": city["name"],
        "attractions": [
            {"name": f"{city['name']}著名景点1", "type": "景点", "duration": "3小时", "ticket": 50},
            {"name": f"{city['name']}著名景点2", "type": "景点", "duration": "4小时", "ticket": 60},
        ]
    }


@router.get("/regions")
async def list_regions():
    """List all regions."""
    regions = list(set(c["region"] for c in CITIES))
    return {"regions": regions}


@router.get("/tags")
async def list_tags():
    """List all tags."""
    all_tags = set()
    for city in CITIES:
        all_tags.update(city.get("tags", []))
    return {"tags": list(all_tags)}
