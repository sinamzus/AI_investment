"""
پیکربندی سیستم بهینه‌سازی پرامپت طراحی داخلی
Configuration for Interior Design Prompt Optimization System
"""

import os
from pathlib import Path

# مدل‌های Fal.ai برای تولید تصویر
FAL_MODELS = {
    "flux-pro": "fal-ai/flux-pro",
    "flux-dev": "fal-ai/flux/dev",
    "flux-realism": "fal-ai/flux-realism",
    "sd3": "fal-ai/stable-diffusion-v3-medium",
}

# تنظیمات پیش‌فرض تصویر
DEFAULT_IMAGE_SIZE = "1024x1024"
DEFAULT_IMAGE_WIDTH = 1024
DEFAULT_IMAGE_HEIGHT = 1024

# مسیر ذخیره نتایج
BASE_DIR = Path(__file__).parent
RESULTS_DIR = BASE_DIR / "results"
HISTORY_FILE = RESULTS_DIR / "history.json"

# مدل آنتروپیک برای تولید و ارزیابی پرامپت
ANTHROPIC_MODEL = "claude-sonnet-4-6"

# تعداد فرمت‌های پرامپت که تولید می‌شوند
NUM_PROMPT_FORMATS = 6

# فرمت‌های پرامپت و توضیح آن‌ها
PROMPT_FORMATS = {
    "FORMAT_A": "Simple Natural Language (1-2 sentences)",
    "FORMAT_B": "Detailed Descriptive Prose (3-4 sentences)",
    "FORMAT_C": "Keyword/Tag Style (comma-separated key terms)",
    "FORMAT_D": "Technical/Structured (with quality modifiers)",
    "FORMAT_E": "Style-First Approach (start with artistic/architectural style)",
    "FORMAT_F": "Atmosphere/Mood Focused (sensory and emotional descriptors)",
}

# معیارهای ارزیابی طراحی داخلی
EVALUATION_CRITERIA = {
    "design_coherence": "Design Coherence (0-10): Does the image match the stated concept?",
    "interior_quality": "Interior Design Quality (0-10): Professionally designed, realistic proportions, proper furniture arrangement?",
    "aesthetic_appeal": "Aesthetic Appeal (0-10): Beautiful, pleasing composition?",
    "technical_quality": "Technical Quality (0-10): Lighting, detail, photorealism?",
    "usability": "Usability (0-10): Is this something a client would approve?",
}

# تعداد تلاش مجدد برای خطاها
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

# رنگ‌های نمایش در CLI
COLORS = {
    "primary": "cyan",
    "secondary": "magenta",
    "success": "green",
    "warning": "yellow",
    "error": "red",
    "info": "blue",
}
