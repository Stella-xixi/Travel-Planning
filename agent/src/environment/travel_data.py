"""
环境交互模块 (Environment)
"""

from typing import Dict, Any, List, Optional


class TravelData:
    """旅游数据环境"""

    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.tools = self._register_tools()

    def _register_tools(self) -> Dict[str, callable]:
        return {
            "search_cities": self.search_cities,
            "query_attractions": self.query_attractions,
            "calculate_budget": self.calculate_budget,
            "get_city_info": self.get_city_info
        }

    def search_cities(self, interests: List[str] = None,
                     budget: tuple = None,
                     season: str = None) -> Dict[str, Any]:
        """根据兴趣、预算、季节搜索城市"""
        all_cities = self.config_manager.get_all_cities()
        matched_cities = []

        for city_name in all_cities:
            city_info = self.config_manager.get_city_info(city_name)
            if not city_info:
                continue

            score = 0
            match_reasons = []

            if interests:
                city_tags = city_info.get('tags', [])
                for interest in interests:
                    if interest in city_tags or any(interest in tag for tag in city_tags):
                        score += 30
                        match_reasons.append(f"符合{interest}兴趣")

            if budget:
                avg_budget = city_info.get('avg_budget_per_day', 0)
                if budget[0] <= avg_budget <= budget[1]:
                    score += 20
                    match_reasons.append("预算适合")
                elif avg_budget < budget[1]:
                    score += 10

            if season:
                best_seasons = city_info.get('best_season', [])
                if season in best_seasons:
                    score += 15
                    match_reasons.append("季节适宜")

            if not interests and not budget and not season:
                score = 50

            if score > 0:
                matched_cities.append({
                    "city": city_name,
                    "score": score,
                    "info": city_info,
                    "match_reasons": match_reasons
                })

        matched_cities.sort(key=lambda x: x['score'], reverse=True)

        return {
            "success": True,
            "cities": matched_cities,
            "count": len(matched_cities)
        }

    def query_attractions(self, cities: List[str]) -> Dict[str, Any]:
        """查询城市的景点信息"""
        result = {}

        for city_name in cities:
            city_info = self.config_manager.get_city_info(city_name)
            if city_info:
                result[city_name] = {
                    "attractions": city_info.get('attractions', []),
                    "avg_budget_per_day": city_info.get('avg_budget_per_day', 0),
                    "recommended_days": city_info.get('recommended_days', 3)
                }
            else:
                # 尝试查找地区对应的城市
                region_cities = self._get_cities_by_region(city_name)
                if region_cities:
                    # 合并所有城市的景点信息
                    for actual_city in region_cities:
                        city_info = self.config_manager.get_city_info(actual_city)
                        if city_info:
                            result[actual_city] = {
                                "attractions": city_info.get('attractions', []),
                                "avg_budget_per_day": city_info.get('avg_budget_per_day', 0),
                                "recommended_days": city_info.get('recommended_days', 3),
                                "region": city_name  # 标记来源地区
                            }

        return {
            "success": True,
            "data": result,
            "cities_count": len(result)
        }

    def calculate_budget(self, city: str, days: int,
                        include_accommodation: bool = True,
                        include_transportation: bool = True) -> Dict[str, Any]:
        """计算旅游预算"""
        city_info = self.config_manager.get_city_info(city)
        if not city_info:
            return {
                "success": False,
                "error": f"未找到城市: {city}"
            }

        avg_daily = city_info.get('avg_budget_per_day', 400)
        attractions = city_info.get('attractions', [])

        ticket_total = sum(a.get('ticket', 0) for a in attractions)
        meal_cost = avg_daily * 0.4 * days
        local_transport = avg_daily * 0.2 * days

        budget = {
            "tickets": ticket_total,
            "meals": int(meal_cost),
            "local_transportation": int(local_transport)
        }

        if include_accommodation:
            accommodation = avg_daily * 0.3 * days
            budget['accommodation'] = int(accommodation)

        if include_transportation:
            inter_city_transport = 1000
            budget['inter_city_transportation'] = inter_city_transport

        budget['total'] = sum(budget.values())
        budget['days'] = days
        budget['avg_per_day'] = int(budget['total'] / days)

        return {
            "success": True,
            "city": city,
            "budget": budget
        }

    def get_city_info(self, city: str) -> Dict[str, Any]:
        """获取城市详细信息"""
        city_info = self.config_manager.get_city_info(city)
        if city_info:
            return {
                "success": True,
                "city": city,
                "info": city_info
            }
        else:
            # 尝试查找地区对应的城市
            region_cities = self._get_cities_by_region(city)
            if region_cities:
                # 返回地区信息，包含所有城市
                first_city = region_cities[0]
                city_info = self.config_manager.get_city_info(first_city)
                if city_info:
                    # 使用地区名称，但包含实际城市信息
                    return {
                        "success": True,
                        "city": city,
                        "info": {
                            **city_info,
                            "name": city,
                            "is_region": True,
                            "cities": region_cities
                        }
                    }
            return {
                "success": False,
                "error": f"未找到城市: {city}"
            }

    def _get_cities_by_region(self, region: str) -> List[str]:
        """根据地区名称获取该地区的所有城市"""
        all_cities = self.config_manager.get_all_cities()
        region_cities = []
        for city_name in all_cities:
            city_info = self.config_manager.get_city_info(city_name)
            if city_info and city_info.get('region') == region:
                region_cities.append(city_name)
        return region_cities

    def execute_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """执行工具调用"""
        if tool_name not in self.tools:
            return {
                "success": False,
                "error": f"工具不存在: {tool_name}"
            }

        try:
            return self.tools[tool_name](**kwargs)
        except Exception as e:
            return {
                "success": False,
                "error": f"工具执行失败: {str(e)}"
            }
