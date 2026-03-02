import time
from uuid import UUID


def run_ai_reconstruction(job_id: UUID):
    """
    Simulates the AI-based reconstruction pipeline.

    RULES:
    - DO NOT manage job state here
    - Raise exceptions on failure
    - Return normally on success
    """

    try:
        print(f"[AI] Starting AI reconstruction for job {job_id}")

        # Step 1: Load AI model
        print("[AI] Step 1: Loading AI model...")
        time.sleep(1)

        # Step 2: Preprocess images
        print("[AI] Step 2: Preprocessing images...")
        time.sleep(1)

        # Step 3: Run inference
        print("[AI] Step 3: Running inference...")
        time.sleep(2)

        # Step 4: Postprocessing
        print("[AI] Step 4: Postprocessing results...")
        time.sleep(1)

        print(f"[AI] AI reconstruction pipeline completed for job {job_id}")

    except Exception as e:
        print(f"[AI] Pipeline failed for job {job_id}: {e}")
        raise
