from util import ProgressTracker
from agents import RunContextWrapper

def read_progress_tracker(wrapper: RunContextWrapper[ProgressTracker]) -> ProgressTracker:
    """
    Read the progress tracker.

    Returns:
        The progress tracker.
    """
    return wrapper.context.get_progress_tracker()

def update_progress_tracker(wrapper: RunContextWrapper[ProgressTracker], stage: str, key_observations: list[str] = None) -> ProgressTracker:
    """
    Update the progress tracker.

    Args:
        stage: The stage to update the progress tracker to.
        key_observations: The key observations to update the progress tracker with.

    Returns:
        The updated progress tracker.
    """
    progress_tracker = wrapper.context.get_progress_tracker()
    progress_tracker.update(stage, key_observations)
    return progress_tracker

def rewrite_observations_tool(wrapper: RunContextWrapper[ProgressTracker], key_observations: list[str]) -> ProgressTracker:
    """
    Rewrite the key observations if they get too long.
    Args:
        key_observations: The key observations to rewrite.

    Returns:
        The updated progress tracker.
    """
    progress_tracker = wrapper.context.get_progress_tracker()
    progress_tracker.rewrite(key_observations)
    return progress_tracker