# app/constants.py

# -----------------------------
# IMAGE UPLOAD RULES
# -----------------------------

# Minimum number of images required to start a job
MIN_IMAGES_PER_JOB = 5

# Maximum number of images allowed per job
MAX_IMAGES_PER_JOB = 200


# -----------------------------
# JOB STATES
# -----------------------------

JOB_STATUS_CREATED = "created"
JOB_STATUS_UPLOADING = "uploading"
JOB_STATUS_PENDING = "pending"
JOB_STATUS_PROCESSING = "processing"
JOB_STATUS_COMPLETED = "completed"
JOB_STATUS_FAILED = "failed"


# -----------------------------
# UPLOAD CONTROL
# -----------------------------

# States in which image upload is allowed
UPLOAD_ALLOWED_STATES = {
    JOB_STATUS_CREATED,
    JOB_STATUS_UPLOADING
}
