"""
ردیاب نتایج و تاریخچه بهینه‌سازی
Results tracker and optimization history storage in JSON
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from collections import defaultdict

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from config import HISTORY_FILE, RESULTS_DIR

console = Console()


class ResultsTracker:
    """
    ردیاب نتایج برای ذخیره و بازیابی تاریخچه بهینه‌سازی
    Tracks and persists optimization results across sessions
    """

    def __init__(self):
        # اطمینان از وجود پوشه results
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        self.history: List[Dict] = []
        self.load_history()

    def load_history(self) -> None:
        """بارگذاری تاریخچه از فایل JSON"""
        if HISTORY_FILE.exists():
            try:
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    self.history = json.load(f)
                console.print(f"[dim]Loaded {len(self.history)} historical records.[/dim]")
            except (json.JSONDecodeError, IOError) as e:
                console.print(f"[yellow]Warning: Could not load history: {e}. Starting fresh.[/yellow]")
                self.history = []
        else:
            self.history = []

    def save_history(self) -> None:
        """ذخیره تاریخچه در فایل JSON"""
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        try:
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except IOError as e:
            console.print(f"[red]Failed to save history: {e}[/red]")

    def add_result(
        self,
        concept: str,
        format_type: str,
        format_name: str,
        prompt_text: str,
        model: str,
        image_path: Optional[str],
        scores: Dict[str, float],
        user_rating: Optional[int] = None,
        user_feedback: Optional[str] = None,
        iteration: int = 1,
        session_id: Optional[str] = None,
    ) -> None:
        """
        اضافه کردن یک نتیجه به تاریخچه
        Add a single result record to the history
        """
        record = {
            "id": f"{int(time.time())}_{format_type}_{model}",
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id or datetime.now().strftime("%Y%m%d_%H%M%S"),
            "iteration": iteration,
            "concept": concept,
            "format_type": format_type,          # e.g. FORMAT_A
            "format_name": format_name,          # e.g. Simple Natural Language
            "prompt_text": prompt_text,
            "model": model,                      # e.g. flux-pro
            "image_path": image_path,
            "scores": {
                "design_coherence": scores.get("design_coherence", 0.0),
                "interior_quality": scores.get("interior_quality", 0.0),
                "aesthetic_appeal": scores.get("aesthetic_appeal", 0.0),
                "technical_quality": scores.get("technical_quality", 0.0),
                "usability": scores.get("usability", 0.0),
                "total": scores.get("total", 0.0),
            },
            "user_rating": user_rating,          # امتیاز کاربر 1-5
            "user_feedback": user_feedback,      # متن بازخورد کاربر
        }
        self.history.append(record)
        self.save_history()

    def add_results_batch(
        self,
        concept: str,
        evaluation_results: list,
        user_ratings: Optional[Dict[str, int]] = None,
        user_feedback: Optional[str] = None,
        iteration: int = 1,
        session_id: Optional[str] = None,
    ) -> None:
        """
        اضافه کردن دسته‌ای از نتایج به تاریخچه
        Add a batch of evaluation results at once
        """
        from config import PROMPT_FORMATS
        sid = session_id or datetime.now().strftime("%Y%m%d_%H%M%S")

        for ev in evaluation_results:
            # پیدا کردن نام فرمت
            format_name = PROMPT_FORMATS.get(ev.format_name, ev.format_name)

            key = f"{ev.format_name}_{ev.model_name}"
            user_rating = (user_ratings or {}).get(key)

            scores = {
                "design_coherence": ev.design_coherence,
                "interior_quality": ev.interior_quality,
                "aesthetic_appeal": ev.aesthetic_appeal,
                "technical_quality": ev.technical_quality,
                "usability": ev.usability,
                "total": ev.total_score,
            }

            self.add_result(
                concept=concept,
                format_type=ev.format_name,
                format_name=format_name,
                prompt_text=ev.prompt_text,
                model=ev.model_name,
                image_path=ev.image_path,
                scores=scores,
                user_rating=user_rating,
                user_feedback=user_feedback,
                iteration=iteration,
                session_id=sid,
            )

    def get_analytics(self) -> Dict[str, Any]:
        """
        تحلیل الگوهای نتایج: بهترین فرمت برای هر مدل، بهترین مدل برای هر مفهوم
        Analyze patterns: best format per model, best model, etc.
        """
        if not self.history:
            return {}

        analytics = {
            "total_records": len(self.history),
            "best_format_per_model": {},
            "best_model_overall": None,
            "best_format_overall": None,
            "model_avg_scores": {},
            "format_avg_scores": {},
            "top_combinations": [],
        }

        # گروه‌بندی بر اساس مدل
        model_scores: Dict[str, List[float]] = defaultdict(list)
        format_scores: Dict[str, List[float]] = defaultdict(list)
        combo_scores: Dict[str, List[float]] = defaultdict(list)

        for record in self.history:
            total = record["scores"].get("total", 0)
            model = record["model"]
            fmt = record["format_type"]
            combo = f"{model}/{fmt}"

            model_scores[model].append(total)
            format_scores[fmt].append(total)
            combo_scores[combo].append(total)

        # میانگین امتیاز هر مدل
        for model, scores in model_scores.items():
            analytics["model_avg_scores"][model] = round(sum(scores) / len(scores), 2)

        # میانگین امتیاز هر فرمت
        for fmt, scores in format_scores.items():
            analytics["format_avg_scores"][fmt] = round(sum(scores) / len(scores), 2)

        # بهترین مدل کلی
        if analytics["model_avg_scores"]:
            best_model = max(analytics["model_avg_scores"], key=analytics["model_avg_scores"].get)
            analytics["best_model_overall"] = {
                "model": best_model,
                "avg_score": analytics["model_avg_scores"][best_model],
            }

        # بهترین فرمت کلی
        if analytics["format_avg_scores"]:
            best_fmt = max(analytics["format_avg_scores"], key=analytics["format_avg_scores"].get)
            analytics["best_format_overall"] = {
                "format": best_fmt,
                "avg_score": analytics["format_avg_scores"][best_fmt],
            }

        # بهترین فرمت برای هر مدل
        model_format_scores: Dict[str, Dict[str, List[float]]] = defaultdict(lambda: defaultdict(list))
        for record in self.history:
            m = record["model"]
            f = record["format_type"]
            model_format_scores[m][f].append(record["scores"].get("total", 0))

        for model, fmt_data in model_format_scores.items():
            avg_by_fmt = {f: sum(s) / len(s) for f, s in fmt_data.items()}
            best_fmt = max(avg_by_fmt, key=avg_by_fmt.get)
            analytics["best_format_per_model"][model] = {
                "format": best_fmt,
                "avg_score": round(avg_by_fmt[best_fmt], 2),
            }

        # برترین ترکیب‌ها (combo)
        combo_avgs = {c: sum(s) / len(s) for c, s in combo_scores.items()}
        top_combos = sorted(combo_avgs.items(), key=lambda x: x[1], reverse=True)[:5]
        analytics["top_combinations"] = [
            {"combo": c, "avg_score": round(s, 2)} for c, s in top_combos
        ]

        return analytics

    def generate_summary_report(self) -> None:
        """
        تولید گزارش خلاصه پیشرفت بهینه‌سازی
        Generate a summary report showing optimization progress
        """
        analytics = self.get_analytics()

        if not analytics:
            console.print(Panel(
                "[yellow]No history data yet. Run some optimization rounds first.[/yellow]",
                title="Optimization History",
                border_style="yellow",
            ))
            return

        console.print(Panel(
            f"[bold cyan]Total experiments: {analytics['total_records']}[/bold cyan]",
            title="[bold]Optimization History Summary[/bold]",
            border_style="cyan",
        ))

        # جدول میانگین امتیاز مدل‌ها
        model_table = Table(
            title="Average Score by Model",
            box=box.SIMPLE_HEAVY,
            border_style="cyan",
        )
        model_table.add_column("Model", style="cyan")
        model_table.add_column("Avg Score", justify="center", style="bold")
        model_table.add_column("Best Format", style="magenta")

        for model, avg in sorted(
            analytics["model_avg_scores"].items(), key=lambda x: x[1], reverse=True
        ):
            best_fmt_info = analytics["best_format_per_model"].get(model, {})
            best_fmt = best_fmt_info.get("format", "N/A")
            color = "green" if avg >= 7 else "yellow" if avg >= 5 else "red"
            model_table.add_row(model, f"[{color}]{avg:.2f}[/{color}]", best_fmt)

        console.print(model_table)

        # جدول میانگین امتیاز فرمت‌ها
        fmt_table = Table(
            title="Average Score by Format",
            box=box.SIMPLE_HEAVY,
            border_style="magenta",
        )
        fmt_table.add_column("Format", style="magenta")
        fmt_table.add_column("Avg Score", justify="center", style="bold")

        for fmt, avg in sorted(
            analytics["format_avg_scores"].items(), key=lambda x: x[1], reverse=True
        ):
            color = "green" if avg >= 7 else "yellow" if avg >= 5 else "red"
            fmt_table.add_row(fmt, f"[{color}]{avg:.2f}[/{color}]")

        console.print(fmt_table)

        # برترین ترکیب‌ها
        if analytics["top_combinations"]:
            combo_table = Table(
                title="Top Model+Format Combinations",
                box=box.SIMPLE_HEAVY,
                border_style="yellow",
            )
            combo_table.add_column("Rank", justify="center")
            combo_table.add_column("Combination", style="white")
            combo_table.add_column("Avg Score", justify="center", style="bold")

            for i, combo_data in enumerate(analytics["top_combinations"], 1):
                color = "green" if combo_data["avg_score"] >= 7 else "yellow"
                combo_table.add_row(
                    f"#{i}",
                    combo_data["combo"],
                    f"[{color}]{combo_data['avg_score']:.2f}[/{color}]",
                )

            console.print(combo_table)

        # نمایش بهترین‌ها به طور کلی
        if analytics.get("best_model_overall"):
            best_model = analytics["best_model_overall"]
            best_fmt = analytics["best_format_overall"]
            console.print(Panel(
                f"[green]Best Model:[/green] {best_model['model']} (avg: {best_model['avg_score']:.2f})\n"
                f"[cyan]Best Format:[/cyan] {best_fmt['format']} (avg: {best_fmt['avg_score']:.2f})",
                title="Overall Winners",
                border_style="green",
            ))

    def get_best_formats_for_refinement(self, n: int = 2) -> List[Dict]:
        """
        بازیابی بهترین فرمت‌ها برای استفاده در مرحله بعدی بهینه‌سازی
        Get the top N best-performing format records for refinement
        """
        if not self.history:
            return []

        # مرتب‌سازی بر اساس امتیاز کل
        sorted_records = sorted(
            self.history,
            key=lambda r: r["scores"].get("total", 0),
            reverse=True,
        )
        return sorted_records[:n]
