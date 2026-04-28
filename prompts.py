"""
Prompt library for Fashn AI product-to-model generation.
Each prompt is pre-tested for consistent, high-quality outputs.
"""

# Base components
# Line ~12 - Update BASE_STUDIO:
BASE_STUDIO = "white studio background, natural catalog lighting, hyper-realistic e-commerce photography, sharp focus, full-body shot head to toe, same exact footwear in all three views consistent across front back and side"# ===================================================================
# POSE LIBRARIES (5-6 variations per view)
# ===================================================================

FRONT_POSES = [
    "full front view, weight on one leg, hand touching hair, relaxed confident stance",
    "full front view, arms crossed casually, slight smile, natural posture",
    "full front view, one hand on hip, other arm relaxed, editorial pose",
    "full front view, both hands in pockets, leaning slightly, casual stance",
    "full front view, arms at sides, walking motion mid-step, dynamic energy",
]

BACK_POSES = [
    "full back view, looking over shoulder, hand on hip, confident stance",
    "full back view, both hands touching hair, relaxed posture",
    "full back view, one hand behind neck, natural casual pose",
    "full back view, arms at sides, mid-walk motion, dynamic",
    "full back view, looking back slightly, arms relaxed, editorial stance",
]

SIDE_POSES = [
    "three-quarter angled view 45 degrees, both arms at sides, natural stance",
    "three-quarter angled view 45 degrees, hand on hip, weight shifted, confident",
    "three-quarter angled view 45 degrees, arms crossed, leaning back slightly, casual",
    "three-quarter angled view 45 degrees, one hand touching face, editorial pose",
    "three-quarter angled view 45 degrees, both arms at sides, natural stance",
]

# Footwear by category
FOOTWEAR = {
    "dresses": "heels",
    "tops": "white sneakers",
    "blouses": "white sneakers",
    "shirts": "white sneakers",
    "tees": "white sneakers",
    "pants": "white sneakers",
    "shorts": "white sneakers",
    "jeans": "white sneakers",
    "trousers": "white sneakers",
    "skirts": "heels",
    "default": "appropriate footwear"
}


def get_footwear(category: str) -> str:
    """Get appropriate footwear for category."""
    category_lower = category.lower()
    for key, footwear in FOOTWEAR.items():
        if key in category_lower:
            return footwear
    return FOOTWEAR["default"]


def _rotate_pose(pose_list: list, product_index: int) -> str:
    """Get pose using round-robin based on product index."""
    return pose_list[product_index % len(pose_list)]


# ===================================================================
# FRONT VIEW PROMPTS
# ===================================================================

def front_prompt(category: str, product_index: int) -> str:
    """Front view prompt with rotating poses."""
    footwear = get_footwear(category)
    pose = _rotate_pose(FRONT_POSES, product_index)
    return f"{pose}, wearing {category.lower()} with {footwear} same footwear for all views, {BASE_STUDIO}"


# ===================================================================
# BACK VIEW PROMPTS
# ===================================================================

def back_prompt_with_input(category: str, product_index: int) -> str:
    """Back view when we have actual back image input."""
    footwear = get_footwear(category)
    pose = _rotate_pose(BACK_POSES, product_index)
    return f"{pose}, wearing {category.lower()} with {footwear}, preserve exact original back design from product image, do not modify back details, do not add embellishments, replicate back precisely as shown in input, same footwear for all views, {BASE_STUDIO}"

def back_prompt_no_input(category: str, product_index: int) -> str:
    """Back view when NO back image (prevent hallucination)."""
    footwear = get_footwear(category)
    pose = _rotate_pose(BACK_POSES, product_index)
    return f"{pose}, wearing {category.lower()} with {footwear} same footwear for all views, plain simple back with no added details or embellishments, {BASE_STUDIO}"


# ===================================================================
# SIDE VIEW PROMPTS
# ===================================================================

def side_prompt(category: str, product_index: int) -> str:
    """Side/angled view prompt with rotating poses."""
    footwear = get_footwear(category)
    pose = _rotate_pose(SIDE_POSES, product_index)
    return f"{pose}, wearing {category.lower()} with {footwear} same footwear for all views, {BASE_STUDIO}"