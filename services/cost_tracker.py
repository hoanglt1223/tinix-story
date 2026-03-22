"""
Dịch vụ theo dõi token và chi phí API
Ghi lại usage sau mỗi lần gọi API, tổng hợp theo dự án và backend
"""
import logging
from datetime import datetime
from typing import List, Dict, Optional

from core.database import get_db

logger = logging.getLogger(__name__)


class CostTracker:
    """Theo dõi token sử dụng và ước tính chi phí API"""

    # Bảng giá USD trên 1M token (input / output)
    PRICING = {
        "gpt-4o-mini": {"input": 0.15, "output": 0.6},
        "gpt-4o": {"input": 2.5, "output": 10.0},
        "gpt-4": {"input": 30.0, "output": 60.0},
        "gpt-3.5": {"input": 0.5, "output": 1.5},
        "claude": {"input": 3.0, "output": 15.0},
        "deepseek": {"input": 0.14, "output": 0.28},
        "gemini": {"input": 0.075, "output": 0.3},
        "default": {"input": 1.0, "output": 3.0},
    }

    @staticmethod
    def _get_price(model: str) -> Dict[str, float]:
        """Tìm bảng giá phù hợp dựa trên tên model"""
        model_lower = (model or "").lower()
        for key, price in CostTracker.PRICING.items():
            if key != "default" and key in model_lower:
                return price
        return CostTracker.PRICING["default"]

    @staticmethod
    def log_usage(
        project_id: Optional[str],
        backend_name: str,
        model: str,
        tokens_in: int,
        tokens_out: int,
        operation: str = "generate"
    ) -> None:
        """Ghi lại lượt sử dụng API vào bảng api_usage"""
        try:
            price = CostTracker._get_price(model)
            cost = (tokens_in * price["input"] + tokens_out * price["output"]) / 1_000_000
            now = datetime.now().isoformat()
            conn = get_db()
            conn.execute(
                """INSERT INTO api_usage
                   (project_id, backend_name, model, tokens_in, tokens_out, cost_estimate, operation, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (project_id, backend_name, model, tokens_in, tokens_out, cost, operation, now)
            )
            conn.commit()
            logger.debug(f"Usage logged: {backend_name}/{model} in={tokens_in} out={tokens_out} cost=${cost:.6f}")
        except Exception as e:
            logger.warning(f"log_usage failed: {e}")

    @staticmethod
    def get_project_costs(project_id: str) -> Dict:
        """Tổng hợp chi phí theo dự án"""
        try:
            conn = get_db()
            row = conn.execute(
                """SELECT SUM(tokens_in) as total_in, SUM(tokens_out) as total_out,
                          SUM(cost_estimate) as total_cost, COUNT(*) as calls
                   FROM api_usage WHERE project_id = ?""",
                (project_id,)
            ).fetchone()
            if row:
                return {
                    "tokens_in": row["total_in"] or 0,
                    "tokens_out": row["total_out"] or 0,
                    "cost": row["total_cost"] or 0.0,
                    "calls": row["calls"] or 0,
                }
        except Exception as e:
            logger.warning(f"get_project_costs failed: {e}")
        return {"tokens_in": 0, "tokens_out": 0, "cost": 0.0, "calls": 0}

    @staticmethod
    def get_total_costs() -> Dict:
        """Tổng hợp chi phí toàn hệ thống"""
        try:
            conn = get_db()
            row = conn.execute(
                """SELECT SUM(tokens_in) as total_in, SUM(tokens_out) as total_out,
                          SUM(cost_estimate) as total_cost, COUNT(*) as calls
                   FROM api_usage"""
            ).fetchone()
            if row:
                return {
                    "tokens_in": row["total_in"] or 0,
                    "tokens_out": row["total_out"] or 0,
                    "cost": row["total_cost"] or 0.0,
                    "calls": row["calls"] or 0,
                }
        except Exception as e:
            logger.warning(f"get_total_costs failed: {e}")
        return {"tokens_in": 0, "tokens_out": 0, "cost": 0.0, "calls": 0}

    @staticmethod
    def get_costs_by_backend() -> List[Dict]:
        """Tổng hợp chi phí theo backend"""
        try:
            conn = get_db()
            rows = conn.execute(
                """SELECT backend_name, model,
                          SUM(tokens_in) as total_in, SUM(tokens_out) as total_out,
                          SUM(cost_estimate) as total_cost, COUNT(*) as calls
                   FROM api_usage
                   GROUP BY backend_name, model
                   ORDER BY total_cost DESC"""
            ).fetchall()
            return [
                {
                    "backend_name": r["backend_name"],
                    "model": r["model"],
                    "tokens_in": r["total_in"] or 0,
                    "tokens_out": r["total_out"] or 0,
                    "cost": r["total_cost"] or 0.0,
                    "calls": r["calls"] or 0,
                }
                for r in rows
            ]
        except Exception as e:
            logger.warning(f"get_costs_by_backend failed: {e}")
        return []

    @staticmethod
    def get_costs_by_project() -> List[Dict]:
        """Tổng hợp chi phí theo dự án (kèm tên dự án nếu có)"""
        try:
            conn = get_db()
            rows = conn.execute(
                """SELECT u.project_id, p.title,
                          SUM(u.tokens_in) as total_in, SUM(u.tokens_out) as total_out,
                          SUM(u.cost_estimate) as total_cost, COUNT(*) as calls
                   FROM api_usage u
                   LEFT JOIN projects p ON p.id = u.project_id
                   GROUP BY u.project_id
                   ORDER BY total_cost DESC"""
            ).fetchall()
            return [
                {
                    "project_id": r["project_id"] or "N/A",
                    "title": r["title"] or r["project_id"] or "N/A",
                    "tokens_in": r["total_in"] or 0,
                    "tokens_out": r["total_out"] or 0,
                    "cost": r["total_cost"] or 0.0,
                    "calls": r["calls"] or 0,
                }
                for r in rows
            ]
        except Exception as e:
            logger.warning(f"get_costs_by_project failed: {e}")
        return []
