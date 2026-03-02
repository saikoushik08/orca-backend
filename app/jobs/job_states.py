# app/jobs/job_states.py

from enum import Enum


class JobStatus(str, Enum):
    CREATED = "created"
    UPLOADING = "uploading"
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# -----------------------------
# STATE GROUPS
# -----------------------------

# States in which image uploads are allowed
UPLOAD_ALLOWED_STATES = {
    JobStatus.CREATED,
    JobStatus.UPLOADING,
}

# States in which job can be started
JOB_START_ALLOWED_STATES = {
    JobStatus.CREATED,
    JobStatus.UPLOADING,
}

# Terminal states (no further transitions allowed)
TERMINAL_STATES = {
    JobStatus.COMPLETED,
    JobStatus.FAILED,
}


# -----------------------------
# STATE TRANSITION RULES
# -----------------------------

# Allowed transitions: current_state -> {next_states}
ALLOWED_TRANSITIONS = {
    JobStatus.CREATED: {
        JobStatus.UPLOADING,
        JobStatus.PENDING,
        JobStatus.FAILED,
    },
    JobStatus.UPLOADING: {
        JobStatus.PENDING,
        JobStatus.FAILED,
    },
    JobStatus.PENDING: {
        JobStatus.PROCESSING,
        JobStatus.FAILED,
    },
    JobStatus.PROCESSING: {
        JobStatus.COMPLETED,
        JobStatus.FAILED,
    },
    JobStatus.COMPLETED: set(),
    JobStatus.FAILED: set(),
}


# -----------------------------
# VALIDATION HELPERS
# -----------------------------

def is_terminal_state(status: JobStatus) -> bool:
    return status in TERMINAL_STATES


def can_upload_images(status: JobStatus) -> bool:
    return status in UPLOAD_ALLOWED_STATES


def can_start_job(status: JobStatus) -> bool:
    return status in JOB_START_ALLOWED_STATES


def is_valid_transition(
    current_status: JobStatus,
    next_status: JobStatus
) -> bool:
    """
    Validate whether a job can move from current_status to next_status
    """
    if current_status not in ALLOWED_TRANSITIONS:
        return False

    return next_status in ALLOWED_TRANSITIONS[current_status]
