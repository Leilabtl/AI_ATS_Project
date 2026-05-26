"""
CV processing pipeline — zero Streamlit dependencies.

Separating this logic from the UI layer means it can be unit-tested,
imported by CLI scripts, or swapped to a background worker without
touching any Streamlit code.
"""

import logging
import os
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)


def process_single_cv(uploaded_file, job_description: str, matcher, llm_analyzer=None) -> dict:
    """Run Phase 1 (keyword matching) and optionally Phase 2 (LLM) on one CV.

    Parameters
    ----------
    uploaded_file : file-like object with `.name` and `.getbuffer()`
        Streamlit UploadedFile, or any object with those two attributes.
    job_description : str
        Full text of the job description.
    matcher : EnhancedMatcher
        Pre-initialised Phase 1 matcher instance.
    llm_analyzer : LLMAnalyzer | None
        If provided, Phase 2 (LLM deep analysis) is executed after Phase 1.

    Returns
    -------
    dict
        Result dict from matcher, augmented with ``filename`` and optionally
        ``llm_analysis`` keys.

    Raises
    ------
    Exception
        Any unrecoverable error from the matcher or PDF parser.  The caller
        is responsible for displaying an appropriate error message to the user.
    """
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(uploaded_file.getbuffer())
        temp_path = tmp.name

    try:
        cv_name = Path(uploaded_file.name).stem
        result = matcher.match_cv_to_job(temp_path, job_description, cv_name)
        result['filename'] = uploaded_file.name

        if llm_analyzer is not None:
            llm_result = llm_analyzer.analyze_candidate(
                result.get('cv_text', ''),
                job_description,
                result.get('pre_analysis', {}),
            )
            result['llm_analysis'] = llm_result  # None if the API call failed
            logger.debug("LLM analysis complete for %s", uploaded_file.name)

        return result

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def process_cv_batch(uploaded_files, job_description: str, matcher,
                     llm_analyzer=None, progress_cb=None, status_cb=None):
    """Process a list of CV files and return (results, errors).

    Parameters
    ----------
    uploaded_files : list
        List of uploaded file objects.
    job_description : str
        Full text of the job description.
    matcher : EnhancedMatcher
        Pre-initialised Phase 1 matcher instance.
    llm_analyzer : LLMAnalyzer | None
        Optional Phase 2 analyser.
    progress_cb : callable(float) | None
        Called with a 0.0–1.0 fraction after each file completes.
    status_cb : callable(str) | None
        Called with a human-readable status string before processing each file.

    Returns
    -------
    tuple[list[dict], list[tuple[str, str]]]
        ``(results, errors)`` where errors is a list of ``(filename, message)``
        pairs for files that failed.
    """
    results = []
    errors = []
    total = len(uploaded_files)

    for idx, uploaded_file in enumerate(uploaded_files):
        if status_cb:
            status_cb(f"Processing {idx + 1}/{total}: {uploaded_file.name}")

        try:
            result = process_single_cv(
                uploaded_file, job_description, matcher, llm_analyzer
            )
            results.append(result)
            logger.info("Processed %s — score %.1f", uploaded_file.name,
                        result.get('final_score', 0))
        except Exception as exc:
            logger.error("Failed to process %s: %s", uploaded_file.name, exc)
            errors.append((uploaded_file.name, str(exc)))

        if progress_cb:
            progress_cb((idx + 1) / total)

    return results, errors
