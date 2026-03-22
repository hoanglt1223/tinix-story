"""
Dịch vụ kiểm tra tính nhất quán nội dung truyện bằng AI
Phát hiện mâu thuẫn tên nhân vật, timeline, plot holes, tone shifts
"""
import logging
import json
from typing import List, Dict

from services.api_client import get_api_client
from core.database import get_db
from locales.i18n import t

logger = logging.getLogger(__name__)


class ConsistencyChecker:
    """Kiểm tra tính nhất quán nội dung các chương truyện"""

    @staticmethod
    def check_project(project_id: str) -> List[Dict]:
        """
        Quét toàn bộ dự án tìm mâu thuẫn nội dung.
        Trả về danh sách {type, severity, chapter, description, suggestion}
        """
        conn = get_db()
        chapters = conn.execute(
            "SELECT num, title, content FROM chapters WHERE project_id = ? AND content != '' ORDER BY num",
            (project_id,)
        ).fetchall()

        if not chapters or len(chapters) < 2:
            return []

        issues = []
        # Kiểm tra từng nhóm 3 chương
        for i in range(0, len(chapters), 3):
            chunk = chapters[i:i + 3]
            chunk_issues = ConsistencyChecker._check_chunk(chunk)
            issues.extend(chunk_issues)

        # Sắp xếp theo mức độ nghiêm trọng
        severity_order = {"critical": 0, "warning": 1, "info": 2}
        return sorted(issues, key=lambda x: severity_order.get(x.get("severity", "info"), 2))

    @staticmethod
    def _check_chunk(chapters) -> List[Dict]:
        """Gọi AI phân tích mâu thuẫn trong một nhóm chương"""
        text = ""
        for ch in chapters:
            content_preview = (ch["content"] or "")[:2000]
            text += f"\n--- Chapter {ch['num']}: {ch['title']} ---\n{content_preview}\n"

        prompt = (
            "Analyze these novel chapters for consistency issues. Find:\n"
            "1. Character name variations/misspellings\n"
            "2. Timeline contradictions\n"
            "3. Plot holes\n"
            "4. Tone shifts\n\n"
            f"{text}\n\n"
            "Return a JSON array of issues. Each issue: "
            '{"type": "name_variation|timeline_error|plot_hole|tone_shift", '
            '"severity": "critical|warning|info", '
            '"chapter": <num>, '
            '"description": "...", '
            '"suggestion": "..."}\n'
            "If no issues found, return empty array []."
        )

        messages = [
            {"role": "system", "content": "You are a novel consistency checker. Always return valid JSON array only, no extra text."},
            {"role": "user", "content": prompt}
        ]

        api = get_api_client()
        success, response = api.generate(messages, use_cache=False)
        if not success:
            logger.warning(f"Consistency check API call failed: {response}")
            return []

        return ConsistencyChecker._parse_response(response)

    @staticmethod
    def _parse_response(response: str) -> List[Dict]:
        """Phân tích phản hồi JSON từ AI"""
        try:
            response = response.strip()
            # Loại bỏ code block markdown nếu có
            if response.startswith("```"):
                response = response.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
            result = json.loads(response)
            if isinstance(result, list):
                # Lọc chỉ giữ các issue có đủ trường cần thiết
                valid = []
                for item in result:
                    if isinstance(item, dict) and "description" in item:
                        valid.append(item)
                return valid
        except (json.JSONDecodeError, Exception) as e:
            logger.warning(f"Failed to parse consistency check response: {e}")
        return []

    @staticmethod
    def format_report(issues: List[Dict]) -> str:
        """Định dạng báo cáo Markdown từ danh sách issue"""
        if not issues:
            return f"✅ {t('consistency.no_issues_found')}"

        severity_icons = {"critical": "🔴", "warning": "🟡", "info": "🔵"}
        type_labels = {
            "name_variation": t("consistency.type_name_variation"),
            "timeline_error": t("consistency.type_timeline_error"),
            "plot_hole": t("consistency.type_plot_hole"),
            "tone_shift": t("consistency.type_tone_shift"),
        }

        lines = [f"## {t('consistency.report_header')} ({len(issues)} {t('consistency.issues_count')})\n"]

        for issue in issues:
            severity = issue.get("severity", "info")
            icon = severity_icons.get(severity, "🔵")
            issue_type = issue.get("type", "")
            label = type_labels.get(issue_type, issue_type)
            chapter = issue.get("chapter", "?")
            desc = issue.get("description", "")
            suggestion = issue.get("suggestion", "")

            lines.append(f"{icon} **[{label}]** — {t('consistency.chapter_label')} {chapter}")
            lines.append(f"- {desc}")
            if suggestion:
                lines.append(f"- 💡 {t('consistency.suggestion_label')}: {suggestion}")
            lines.append("")

        return "\n".join(lines)
