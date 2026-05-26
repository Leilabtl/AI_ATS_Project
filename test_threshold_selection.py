"""
QA tests for the Score Threshold selection feature.

Covers three test scenarios:
  TC-1  Exact boundary categorisation (on / above / below thresholds)
  TC-2  Boundary integrity validation (longlist >= shortlist → ValueError)
  TC-3  Batch processing: assorted scores produce exact expected statuses
"""

import unittest
from unittest.mock import patch, MagicMock
from candidate_pool import CandidatePool


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_result(score: float, filename: str = "cv.pdf") -> dict:
    """Minimal result dict that satisfies CandidatePool.add_candidate."""
    return {
        'final_score': score,
        'filename': filename,
        'candidate_email': f"test_{score}@example.com",
        'cv_seniority': 'mid',
        'matched_skills': [],
        'missing_skills': [],
        'confidence_level': 'High',
        'skill_proficiency': {},
        'score_breakdown': {},
        'strategic_summary': '',
        'improvement_areas': [],
    }


def _pool_no_io() -> CandidatePool:
    """Return a CandidatePool instance with all file I/O suppressed."""
    with patch('candidate_pool.os.path.exists', return_value=False):
        pool = CandidatePool(pool_file="_test_pool_dummy.json")
    pool._save_pool = MagicMock()         # silence writes
    pool._ensure_job_folder = MagicMock(return_value="/tmp/fake")
    pool.add_job = MagicMock(return_value="job_001")
    return pool


def _run_threshold(pool, results, shortlist_th, longlist_th):
    """Exercise auto_assign_candidates in Score Threshold mode."""
    with patch.object(pool, 'add_candidate', side_effect=lambda r, *a, **kw: dict(r)):
        _, assigned = pool.auto_assign_candidates(
            results,
            job_title="Test Role",
            job_description="Test JD",
            shortlist_threshold=shortlist_th,
            longlist_threshold=longlist_th,
            use_ranking_mode=False,
        )
    return assigned


def _run_ranking(pool, results, shortlist_count, longlist_count):
    """Exercise auto_assign_candidates in Ranking-Based mode."""
    with patch.object(pool, 'add_candidate', side_effect=lambda r, *a, **kw: dict(r)):
        _, assigned = pool.auto_assign_candidates(
            results,
            job_title="Test Role",
            job_description="Test JD",
            shortlist_threshold=70,
            longlist_threshold=50,
            use_ranking_mode=True,
            shortlist_count=shortlist_count,
            longlist_count=longlist_count,
        )
    return assigned


# ── TC-1: Exact boundary categorisation ───────────────────────────────────────

class TestBoundaryCategorisation(unittest.TestCase):
    """TC-1: Candidates exactly on, above, and below each threshold boundary."""

    SHORTLIST_TH = 70
    LONGLIST_TH  = 50

    def setUp(self):
        self.pool = _pool_no_io()

    def _assign(self, score):
        result = _make_result(score)
        assigned = _run_threshold(self.pool, [result], self.SHORTLIST_TH, self.LONGLIST_TH)
        for bucket, entries in assigned.items():
            for e in entries:
                if e['final_score'] == score:
                    return bucket
        raise AssertionError(f"Score {score} not found in any bucket")

    # ── Shortlist boundary ─────────────────────────────────────────────────────
    def test_score_exactly_on_shortlist_threshold_is_shortlisted(self):
        self.assertEqual(self._assign(70.0), 'shortlist')

    def test_score_above_shortlist_threshold_is_shortlisted(self):
        self.assertEqual(self._assign(85.5), 'shortlist')

    def test_score_just_below_shortlist_threshold_is_not_shortlisted(self):
        self.assertNotEqual(self._assign(69.9), 'shortlist')

    # ── Longlist boundary ──────────────────────────────────────────────────────
    def test_score_exactly_on_longlist_threshold_is_longlisted(self):
        self.assertEqual(self._assign(50.0), 'longlist')

    def test_score_above_longlist_below_shortlist_is_longlisted(self):
        self.assertEqual(self._assign(60.0), 'longlist')

    def test_score_just_below_longlist_threshold_is_rejected(self):
        self.assertEqual(self._assign(49.9), 'rejected')

    def test_score_zero_is_rejected(self):
        self.assertEqual(self._assign(0.0), 'rejected')

    def test_score_100_is_shortlisted(self):
        self.assertEqual(self._assign(100.0), 'shortlist')


# ── TC-2: Boundary integrity validation ───────────────────────────────────────

class TestBoundaryIntegrity(unittest.TestCase):
    """TC-2: Invalid threshold configurations must raise ValueError."""

    def setUp(self):
        self.pool = _pool_no_io()

    def _call(self, shortlist_th, longlist_th):
        return self.pool.auto_assign_candidates(
            [_make_result(60)],
            job_title="Test",
            job_description="Test JD",
            shortlist_threshold=shortlist_th,
            longlist_threshold=longlist_th,
            use_ranking_mode=False,
        )

    def test_equal_thresholds_raise_value_error(self):
        """longlist == shortlist is invalid — both thresholds are the same boundary."""
        with self.assertRaises(ValueError) as ctx:
            self._call(shortlist_th=70, longlist_th=70)
        self.assertIn("longlist_threshold", str(ctx.exception))

    def test_longlist_above_shortlist_raises_value_error(self):
        """longlist > shortlist would invert the buckets."""
        with self.assertRaises(ValueError):
            self._call(shortlist_th=50, longlist_th=70)

    def test_longlist_one_below_shortlist_is_valid(self):
        """Minimum valid gap: longlist = shortlist - 1."""
        with patch.object(self.pool, 'add_candidate', side_effect=lambda r, *a, **kw: dict(r)):
            try:
                self._call(shortlist_th=70, longlist_th=69)
            except ValueError:
                self.fail("Thresholds with gap of 1 should be valid")

    def test_zero_longlist_with_nonzero_shortlist_is_valid(self):
        """longlist=0 means any score above 0 qualifies for longlist."""
        with patch.object(self.pool, 'add_candidate', side_effect=lambda r, *a, **kw: dict(r)):
            try:
                self._call(shortlist_th=70, longlist_th=0)
            except ValueError:
                self.fail("longlist=0, shortlist=70 should be valid")

    def test_both_zero_raises_value_error(self):
        """shortlist=0 and longlist=0: equal thresholds → invalid."""
        with self.assertRaises(ValueError):
            self._call(shortlist_th=0, longlist_th=0)


# ── TC-3: Batch processing with assorted scores ────────────────────────────────

class TestBatchProcessing(unittest.TestCase):
    """TC-3: A realistic batch asserts exact bucket membership for each candidate."""

    SHORTLIST_TH = 70
    LONGLIST_TH  = 50

    def setUp(self):
        self.pool = _pool_no_io()

        # (score, expected_bucket)
        self.batch = [
            (92.0, 'shortlist'),   # well above shortlist
            (70.0, 'shortlist'),   # exactly on shortlist boundary
            (71.5, 'shortlist'),   # just above shortlist
            (69.9, 'longlist'),    # just below shortlist
            (60.0, 'longlist'),    # mid-longlist zone
            (50.0, 'longlist'),    # exactly on longlist boundary
            (49.9, 'rejected'),    # just below longlist
            (35.0, 'rejected'),    # mid-rejected zone
            (0.0,  'rejected'),    # absolute floor
        ]

    def _bucket_for_score(self, score, assigned):
        for bucket, entries in assigned.items():
            for e in entries:
                if e['final_score'] == score:
                    return bucket
        raise AssertionError(f"Score {score} missing from all buckets")

    def test_threshold_mode_exact_bucket_for_every_score(self):
        results = [_make_result(s, f"cv_{s}.pdf") for s, _ in self.batch]
        assigned = _run_threshold(self.pool, results, self.SHORTLIST_TH, self.LONGLIST_TH)

        for score, expected in self.batch:
            with self.subTest(score=score, expected=expected):
                actual = self._bucket_for_score(score, assigned)
                self.assertEqual(
                    actual, expected,
                    f"Score {score}% → expected '{expected}', got '{actual}'"
                )

    def test_threshold_mode_total_count_matches_input(self):
        results = [_make_result(s, f"cv_{s}.pdf") for s, _ in self.batch]
        assigned = _run_threshold(self.pool, results, self.SHORTLIST_TH, self.LONGLIST_TH)

        total = sum(len(v) for v in assigned.values())
        self.assertEqual(total, len(self.batch))

    def test_threshold_mode_correct_bucket_sizes(self):
        results = [_make_result(s, f"cv_{s}.pdf") for s, _ in self.batch]
        assigned = _run_threshold(self.pool, results, self.SHORTLIST_TH, self.LONGLIST_TH)

        expected_shortlist = sum(1 for s, _ in self.batch if s >= self.SHORTLIST_TH)
        expected_longlist  = sum(1 for s, _ in self.batch if self.LONGLIST_TH <= s < self.SHORTLIST_TH)
        expected_rejected  = sum(1 for s, _ in self.batch if s < self.LONGLIST_TH)

        self.assertEqual(len(assigned['shortlist']), expected_shortlist)
        self.assertEqual(len(assigned['longlist']),  expected_longlist)
        self.assertEqual(len(assigned['rejected']),  expected_rejected)


# ── TC-4 (bonus): Ranking-Based mode ──────────────────────────────────────────

class TestRankingMode(unittest.TestCase):
    """Ranking-Based mode assigns by position, not score."""

    def setUp(self):
        self.pool = _pool_no_io()

    def test_top_n_go_to_shortlist(self):
        results = [_make_result(s) for s in [90, 80, 70, 60, 50, 40]]
        assigned = _run_ranking(self.pool, results, shortlist_count=2, longlist_count=4)
        shortlist_scores = sorted([e['final_score'] for e in assigned['shortlist']], reverse=True)
        self.assertEqual(shortlist_scores, [90, 80])

    def test_next_band_goes_to_longlist(self):
        results = [_make_result(s) for s in [90, 80, 70, 60, 50, 40]]
        assigned = _run_ranking(self.pool, results, shortlist_count=2, longlist_count=4)
        longlist_scores = sorted([e['final_score'] for e in assigned['longlist']], reverse=True)
        self.assertEqual(longlist_scores, [70, 60])

    def test_remainder_goes_to_rejected(self):
        results = [_make_result(s) for s in [90, 80, 70, 60, 50, 40]]
        assigned = _run_ranking(self.pool, results, shortlist_count=2, longlist_count=4)
        rejected_scores = sorted([e['final_score'] for e in assigned['rejected']], reverse=True)
        self.assertEqual(rejected_scores, [50, 40])

    def test_ranking_mode_still_rejects_invalid_thresholds(self):
        with self.assertRaises(ValueError):
            self.pool.auto_assign_candidates(
                [_make_result(60)],
                job_title="Test",
                job_description="JD",
                shortlist_threshold=50,
                longlist_threshold=70,  # inverted
                use_ranking_mode=True,
            )


if __name__ == '__main__':
    unittest.main(verbosity=2)
