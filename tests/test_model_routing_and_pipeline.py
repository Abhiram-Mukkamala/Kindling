import asyncio
import unittest
from unittest.mock import patch, AsyncMock
from typing import List, Dict, Any

from backend import config, llm, prompts, pipeline
from backend.schemas import Draft, DraftList, JudgeResult, CodeFinding, CodeAnalysisResult

class TestModelRoutingAndPipeline(unittest.TestCase):
    def setUp(self):
        # Ensure test settings
        self.orig_drafter = config.DRAFTER_MODEL
        self.orig_judge = config.JUDGE_MODEL
        self.orig_rewrite = config.REWRITE_MODEL
        self.orig_code = config.CODE_MODEL

        config.DRAFTER_MODEL = "nvidia/nemotron-3-ultra-550b-a55b"
        config.JUDGE_MODEL = "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning"
        config.REWRITE_MODEL = "google/gemma-4-31b-it"
        config.CODE_MODEL = "qwen/qwen-2.5-coder-32b-instruct"

    def tearDown(self):
        config.DRAFTER_MODEL = self.orig_drafter
        config.JUDGE_MODEL = self.orig_judge
        config.REWRITE_MODEL = self.orig_rewrite
        config.CODE_MODEL = self.orig_code

    def test_model_routing_resolution(self):
        """Assert each role resolves to its dedicated configured model."""
        self.assertEqual(llm._get_model_for_role("drafter"), "nvidia/nemotron-3-ultra-550b-a55b")
        self.assertEqual(llm._get_model_for_role("judge"), "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning")
        self.assertEqual(llm._get_model_for_role("rewrite"), "google/gemma-4-31b-it")
        self.assertEqual(llm._get_model_for_role("code_analysis"), "qwen/qwen-2.5-coder-32b-instruct")

    def test_drafter_selects_drafter_model(self):
        """Assert Drafter step invokes chat_json with the 'drafter' role."""
        mock_draft = Draft(
            id="d1",
            title="Fix bug in parser",
            context="The parser fails on empty input.",
            files_to_touch=["src/parser.py"],
            acceptance_criteria=["Parser handles empty string"],
            difficulty="beginner",
            source="todo",
        )
        fake_result = (DraftList(drafts=[mock_draft]), 150)

        with patch("backend.llm.chat_json", new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = fake_result
            summary = {"owner": "test", "repo": "repo", "tree": ["src/parser.py"], "readme": "Hello"}
            
            drafts, dur = asyncio.run(pipeline.draft_step(summary))
            
            self.assertEqual(len(drafts), 1)
            mock_chat.assert_called_once()
            role_called = mock_chat.call_args[0][0]
            self.assertEqual(role_called, "drafter")
            self.assertEqual(llm._get_model_for_role(role_called), config.DRAFTER_MODEL)

    def test_judge_selects_judge_model(self):
        """Assert Judge step invokes chat_json with the 'judge' role."""
        draft = Draft(
            id="d1",
            title="Sample Draft",
            context="Some context",
            files_to_touch=["README.md"],
            acceptance_criteria=["Check works"],
            difficulty="beginner",
            source="readme_gap",
        )
        fake_judge = (JudgeResult(score=8, critique="Clear and scoped.", problems=[]), 200)

        with patch("backend.llm.chat_json", new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = fake_judge
            res, dur = asyncio.run(pipeline.judge_one(draft, ["README.md"]))
            
            self.assertEqual(res.score, 8)
            mock_chat.assert_called_once()
            role_called = mock_chat.call_args[0][0]
            self.assertEqual(role_called, "judge")
            self.assertEqual(llm._get_model_for_role(role_called), config.JUDGE_MODEL)

    def test_rewrite_selects_rewrite_model(self):
        """Assert Rewrite step invokes chat_json with the dedicated 'rewrite' role."""
        draft = Draft(
            id="d1",
            title="Initial Title",
            context="Initial Context",
            files_to_touch=["src/index.js"],
            acceptance_criteria=["Initial AC"],
            difficulty="beginner",
            source="todo",
        )
        judge = JudgeResult(score=5, critique="Improve testability", problems=["Vague criteria"])
        rewritten_draft = Draft(
            id="d1",
            title="Polished Title",
            context="Initial Context",
            files_to_touch=["src/index.js"],
            acceptance_criteria=["Concrete AC 1", "Concrete AC 2"],
            difficulty="beginner",
            source="todo",
        )

        with patch("backend.llm.chat_json", new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = (rewritten_draft, 300)
            res, dur = asyncio.run(pipeline.rewrite_one(draft, judge, ["src/index.js"]))
            
            self.assertEqual(res.title, "Polished Title")
            mock_chat.assert_called_once()
            role_called = mock_chat.call_args[0][0]
            self.assertEqual(role_called, "rewrite")
            self.assertEqual(llm._get_model_for_role(role_called), config.REWRITE_MODEL)

    def test_rewrite_failure_falls_back_to_original_draft(self):
        """Assert that if a rewrite call fails, the pipeline safely falls back to the original draft."""
        draft = Draft(
            id="d1",
            title="Original Stable Draft",
            context="Stable Context",
            files_to_touch=["app.py"],
            acceptance_criteria=["Does not crash"],
            difficulty="beginner",
            source="open_issue",
        )
        judge = JudgeResult(score=6, critique="Needs more details", problems=["Missing AC"])

        async def fail_rewrite(*args, **kwargs):
            raise RuntimeError("API timeout or rate limit exceeded")

        events = []
        async def mock_emit(ev):
            events.append(ev)

        with patch("backend.pipeline.judge_one", new_callable=AsyncMock) as mock_j, \
             patch("backend.pipeline.rewrite_one", side_effect=fail_rewrite):
            mock_j.return_value = (judge, 100)
            
            issues = asyncio.run(pipeline.process_drafts([draft], {"tree": ["app.py"]}, mock_emit))
            
            self.assertEqual(len(issues), 1)
            # Final must be the original draft because rewrite failed
            self.assertEqual(issues[0].final.title, "Original Stable Draft")
            self.assertEqual(issues[0].final.context, "Stable Context")

    def test_emitted_event_labels_and_models_used(self):
        """Assert that emitted events and models_used report exact model names for each role."""
        draft = Draft(
            id="d1",
            title="Draft 1",
            context="Context 1",
            files_to_touch=["main.py"],
            acceptance_criteria=["AC 1"],
            difficulty="intermediate",
            source="todo",
        )
        judge = JudgeResult(score=7, critique="Good", problems=[])
        rewritten = Draft(
            id="d1",
            title="Rewritten 1",
            context="Context 1",
            files_to_touch=["main.py"],
            acceptance_criteria=["AC 1", "AC 2"],
            difficulty="intermediate",
            source="todo",
        )

        events = []
        async def mock_emit(ev):
            events.append(ev)

        with patch("backend.pipeline.judge_one", new_callable=AsyncMock) as mock_j, \
             patch("backend.pipeline.rewrite_one", new_callable=AsyncMock) as mock_r:
            mock_j.return_value = (judge, 150)
            mock_r.return_value = (rewritten, 250)

            issues = asyncio.run(pipeline.process_drafts([draft], {"tree": ["main.py"]}, mock_emit, code_model_used=True))

            # Check events
            judge_events = [e for e in events if e.get("step") == "judge"]
            rewrite_events = [e for e in events if e.get("step") == "rewrite"]
            
            self.assertTrue(any(e["model"] == config.JUDGE_MODEL and e["role"] == "judge" for e in judge_events))
            self.assertTrue(any(e["model"] == config.REWRITE_MODEL and e["role"] == "rewrite" for e in rewrite_events))

            # Check models_used
            self.assertEqual(issues[0].models_used["drafter"], config.DRAFTER_MODEL)
            self.assertEqual(issues[0].models_used["judge"], config.JUDGE_MODEL)
            self.assertEqual(issues[0].models_used["rewrite"], config.REWRITE_MODEL)
            self.assertEqual(issues[0].models_used["code_analysis"], config.CODE_MODEL)

    def test_qwen_code_analysis_called_with_source_context(self):
        """Assert Qwen code analysis receives source code context and returns structured findings."""
        summary = {
            "owner": "acme",
            "repo": "widget",
            "source_files": {
                "src/utils.py": "def add(a, b):\n    # BUG: doesn't check types\n    return a + b\n"
            }
        }
        mock_finding = CodeFinding(
            file_path="src/utils.py",
            line_range="2-3",
            severity="medium",
            explanation="Missing input validation on arguments.",
            evidence="return a + b",
        )
        fake_qwen_res = (CodeAnalysisResult(findings=[mock_finding]), 420)

        with patch("backend.llm.chat_json", new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = fake_qwen_res

            findings, dur = asyncio.run(pipeline.code_analysis_step(summary))

            self.assertEqual(len(findings), 1)
            self.assertEqual(findings[0].file_path, "src/utils.py")
            self.assertEqual(findings[0].evidence, "return a + b")

            # Verify prompt received source code
            call_args = mock_chat.call_args[0]
            self.assertEqual(call_args[0], "code_analysis")
            self.assertIn("=== FILE: src/utils.py ===", call_args[2])
            self.assertIn("def add(a, b):", call_args[2])

    def test_graphify_context_injected_into_code_analysis(self):
        """Assert Graphify AST relationships are injected into Qwen's code analysis prompt."""
        summary = {
            "owner": "Abhiram-Mukkamala",
            "repo": "Kindling",
            "source_files": {
                "backend/pipeline.py": "async def run_pipeline(): pass"
            }
        }
        mock_finding = CodeFinding(
            file_path="backend/pipeline.py",
            line_range="1",
            severity="low",
            explanation="Test finding",
            evidence="pass",
        )
        fake_qwen_res = (CodeAnalysisResult(findings=[mock_finding]), 300)

        with patch("backend.llm.chat_json", new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = fake_qwen_res

            findings, dur = asyncio.run(pipeline.code_analysis_step(summary))

            self.assertEqual(len(findings), 1)
            call_args = mock_chat.call_args[0]
            self.assertEqual(call_args[0], "code_analysis")
            # Verify Graphify AST header or relationships are present in the prompt
            self.assertIn("GRAPHIFY CODE GRAPH", call_args[2])
            self.assertIn("backend/pipeline.py", call_args[2])

    def test_empty_repository_does_not_crash_code_analysis(self):
        """Assert empty repos with no source files gracefully return empty findings without crash."""
        summary = {"owner": "acme", "repo": "empty-repo", "source_files": {}}
        findings, dur = asyncio.run(pipeline.code_analysis_step(summary))
        self.assertEqual(findings, [])
        self.assertEqual(dur, 0)

    def test_graphify_summary_endpoint(self):
        """Assert /api/graphify/summary reports valid Graphify graph metrics."""
        from backend.graphify_tools import get_graph_summary
        summary = get_graph_summary()
        self.assertTrue(summary.get("available"))
        self.assertGreater(summary.get("nodes_count", 0), 200)
        self.assertGreater(summary.get("edges_count", 0), 400)
        self.assertGreater(len(summary.get("god_nodes", [])), 0)

if __name__ == "__main__":
    unittest.main()
