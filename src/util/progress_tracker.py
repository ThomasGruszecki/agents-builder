from dataclasses import dataclass, field
from pydantic import BaseModel
@dataclass
class ProgressTracker(BaseModel):
    """
    A class to track the progress of the agents.
    It stores the key observations and the current stage of the agents.
    """
    history: list[str] = field(default_factory=list)
    key_observations: list[str] = field(default_factory=list)
    current_stage: str = "initialization"

    def update(self, stage: str, key_observations: list[str] = None):
        self.current_stage = stage
        self.history.append(f"Stage: {stage}")
        if key_observations:
            self.key_observations.extend(key_observations)
            self.history.append(f"Key Observations: {key_observations}")

    def rewrite(self, key_observations: list[str] = None):
        """Rewrite the key observations if they get too long."""
        if key_observations:
            self.key_observations = key_observations

    def get_progress_report(self) -> str:
        """Get a formatted progress report with current stage and key observations."""
        report = [f"Current Stage: {self.current_stage}"]
        
        if self.history:
            report.append("\nProgress History:")
            report.extend([f"  - {entry}" for entry in self.history])
        
        if self.key_observations:
            report.append("\nKey Observations:")
            report.extend([f"  - {obs}" for obs in self.key_observations])
        
        return "\n".join(report)