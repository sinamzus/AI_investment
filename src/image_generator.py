"""
تولید تصویر با استفاده از مدل‌های مختلف Fal.ai
Image generation using multiple Fal.ai models with async support
"""

import asyncio
import os
import time
import hashlib
import aiohttp
import fal_client
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

from config import (
    FAL_MODELS,
    DEFAULT_IMAGE_WIDTH,
    DEFAULT_IMAGE_HEIGHT,
    RESULTS_DIR,
    MAX_RETRIES,
    RETRY_DELAY,
)

console = Console()


@dataclass
class GenerationResult:
    """نتیجه تولید یک تصویر"""
    model_name: str
    model_id: str
    format_name: str
    prompt_text: str
    image_path: Optional[str]
    image_url: Optional[str]
    success: bool
    error_message: Optional[str]
    generation_time: float
    seed: Optional[int] = None


def _generate_filename(concept: str, format_name: str, model_name: str) -> str:
    """
    تولید نام فایل یکتا برای هر تصویر
    Generate a unique filename for each generated image
    """
    timestamp = int(time.time())
    # خلاصه کردن concept برای نام فایل
    concept_short = concept[:30].replace(" ", "_").replace("/", "-")
    concept_short = "".join(c for c in concept_short if c.isalnum() or c in ("_", "-"))
    filename = f"{concept_short}_{format_name}_{model_name}_{timestamp}.png"
    return filename


async def _download_image(url: str, filepath: Path, session: aiohttp.ClientSession) -> bool:
    """
    دانلود تصویر از URL و ذخیره در مسیر مشخص
    Download image from URL and save to specified path
    """
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=60)) as response:
            if response.status == 200:
                content = await response.read()
                filepath.parent.mkdir(parents=True, exist_ok=True)
                with open(filepath, "wb") as f:
                    f.write(content)
                return True
            else:
                console.print(f"[red]Download failed with status {response.status}[/red]")
                return False
    except Exception as e:
        console.print(f"[red]Download error: {e}[/red]")
        return False


def _generate_single_image_sync(
    model_name: str,
    model_id: str,
    format_name: str,
    prompt_text: str,
    concept: str,
    fal_key: str,
) -> GenerationResult:
    """
    تولید یک تصویر به صورت همزمان با retry logic
    Generate a single image synchronously with retry logic
    """
    os.environ["FAL_KEY"] = fal_key
    start_time = time.time()

    # پارامترهای متفاوت برای مدل‌های مختلف
    base_params = {
        "prompt": prompt_text,
        "image_size": {"width": DEFAULT_IMAGE_WIDTH, "height": DEFAULT_IMAGE_HEIGHT},
        "num_inference_steps": 28,
        "guidance_scale": 7.5,
        "num_images": 1,
        "enable_safety_checker": True,
    }

    # تنظیمات خاص هر مدل
    if model_name == "flux-pro":
        params = {
            "prompt": prompt_text,
            "image_size": "square_hd",
            "num_inference_steps": 28,
            "guidance_scale": 3.5,
            "num_images": 1,
            "enable_safety_checker": True,
            "output_format": "png",
        }
    elif model_name == "flux-dev":
        params = {
            "prompt": prompt_text,
            "image_size": "square_hd",
            "num_inference_steps": 28,
            "guidance_scale": 3.5,
            "num_images": 1,
            "enable_safety_checker": True,
            "output_format": "png",
        }
    elif model_name == "flux-realism":
        params = {
            "prompt": prompt_text,
            "image_size": "square_hd",
            "num_inference_steps": 28,
            "guidance_scale": 3.5,
            "num_images": 1,
            "enable_safety_checker": True,
            "output_format": "png",
        }
    elif model_name == "sd3":
        params = {
            "prompt": prompt_text,
            "image_size": "square_hd",
            "num_inference_steps": 28,
            "guidance_scale": 7.0,
            "num_images": 1,
            "enable_safety_checker": True,
            "output_format": "png",
        }
    else:
        params = base_params

    # تلاش مجدد در صورت خطا
    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            result = fal_client.run(model_id, arguments=params)
            generation_time = time.time() - start_time

            # استخراج URL تصویر
            image_url = None
            if isinstance(result, dict):
                # ساختارهای مختلف پاسخ Fal.ai
                if "images" in result and result["images"]:
                    img = result["images"][0]
                    if isinstance(img, dict):
                        image_url = img.get("url") or img.get("image_url")
                    elif isinstance(img, str):
                        image_url = img
                elif "image" in result:
                    img = result["image"]
                    if isinstance(img, dict):
                        image_url = img.get("url") or img.get("image_url")
                    elif isinstance(img, str):
                        image_url = img
                elif "output" in result and isinstance(result["output"], list):
                    image_url = result["output"][0]

            if not image_url:
                raise ValueError(f"No image URL in response: {result}")

            # دانلود تصویر
            filename = _generate_filename(concept, format_name, model_name)
            filepath = RESULTS_DIR / filename

            # دانلود همزمان
            import requests
            download_response = requests.get(image_url, timeout=60)
            if download_response.status_code == 200:
                filepath.parent.mkdir(parents=True, exist_ok=True)
                with open(filepath, "wb") as f:
                    f.write(download_response.content)

                return GenerationResult(
                    model_name=model_name,
                    model_id=model_id,
                    format_name=format_name,
                    prompt_text=prompt_text,
                    image_path=str(filepath),
                    image_url=image_url,
                    success=True,
                    error_message=None,
                    generation_time=generation_time,
                )
            else:
                raise ValueError(f"Failed to download image: HTTP {download_response.status_code}")

        except Exception as e:
            last_error = str(e)
            if attempt < MAX_RETRIES - 1:
                console.print(f"[yellow]Attempt {attempt + 1} failed for {model_name}/{format_name}: {e}[/yellow]")
                time.sleep(RETRY_DELAY * (attempt + 1))
            continue

    generation_time = time.time() - start_time
    return GenerationResult(
        model_name=model_name,
        model_id=model_id,
        format_name=format_name,
        prompt_text=prompt_text,
        image_path=None,
        image_url=None,
        success=False,
        error_message=last_error,
        generation_time=generation_time,
    )


def generate_images_for_formats(
    formats: Dict[str, str],
    selected_models: List[str],
    concept: str,
    fal_key: str,
    progress_callback=None,
) -> List[GenerationResult]:
    """
    تولید تصاویر برای همه فرمت‌ها و مدل‌های انتخاب‌شده
    Generate images for all format-model combinations, showing progress
    """
    # ساختن لیست همه ترکیب‌ها
    tasks = []
    for format_name, prompt_text in formats.items():
        for model_name in selected_models:
            if model_name in FAL_MODELS:
                tasks.append((format_name, prompt_text, model_name, FAL_MODELS[model_name]))

    total_tasks = len(tasks)
    results = []

    console.print(f"\n[cyan]Generating {total_tasks} images ({len(formats)} formats × {len(selected_models)} models)...[/cyan]\n")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
    ) as progress:
        task_id = progress.add_task("Generating images...", total=total_tasks)

        for format_name, prompt_text, model_name, model_id in tasks:
            progress.update(
                task_id,
                description=f"[cyan]{model_name}[/cyan] + [magenta]{format_name}[/magenta]"
            )

            result = _generate_single_image_sync(
                model_name=model_name,
                model_id=model_id,
                format_name=format_name,
                prompt_text=prompt_text,
                concept=concept,
                fal_key=fal_key,
            )
            results.append(result)

            if result.success:
                console.print(f"  [green]✓[/green] {model_name}/{format_name} — {result.generation_time:.1f}s")
            else:
                console.print(f"  [red]✗[/red] {model_name}/{format_name} — {result.error_message}")

            progress.advance(task_id)

    # خلاصه نتایج
    successful = sum(1 for r in results if r.success)
    console.print(f"\n[bold]Generation complete: {successful}/{total_tasks} successful[/bold]")

    return results


def display_generation_summary(results: List[GenerationResult]) -> None:
    """
    نمایش خلاصه نتایج تولید تصویر
    Display a summary table of generation results
    """
    from rich.table import Table
    from rich import box

    table = Table(
        title="Image Generation Summary",
        box=box.ROUNDED,
        border_style="cyan",
        show_lines=True,
    )

    table.add_column("Model", style="cyan", no_wrap=True)
    table.add_column("Format", style="magenta")
    table.add_column("Status", justify="center")
    table.add_column("Time", justify="right", style="dim")

    for r in results:
        status = "[green]✓ OK[/green]" if r.success else f"[red]✗ FAIL[/red]"
        table.add_row(
            r.model_name,
            r.format_name,
            status,
            f"{r.generation_time:.1f}s",
        )

    console.print(table)
