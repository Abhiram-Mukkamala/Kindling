import sys
import json
from pathlib import Path

# Set utf-8 encoding on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.graphify_tools import get_graph_summary, get_graph_context_for_files, GRAPH_PATH, HTML_PATH

def main():
    print("=" * 70)
    print("🔥 Kindling — Graphify Knowledge Graph Demonstration")
    print("=" * 70)

    summary = get_graph_summary()
    if not summary.get("available"):
        print("[!] Graphify output not found. Please run: graphify update .")
        sys.exit(1)

    print(f"Status:            ACTIVE & EXTRACTED")
    print(f"Graph Artifacts:   {GRAPH_PATH.parent.resolve()}")
    print(f"Total Nodes:       {summary['nodes_count']}")
    print(f"Total Edges:       {summary['edges_count']}")
    print(f"Communities:       {summary['communities_count']}")
    print(f"Interactive View:  http://localhost:8000/api/graphify/view")
    print("=" * 70)

    print("\n[1] TOP 'GOD NODES' (Most connected abstractions in Kindling):")
    for idx, node in enumerate(summary.get("god_nodes", []), 1):
        file_info = f" ({node['file']})" if node.get("file") else ""
        print(f"  {idx}. {node['label']:<24} -> {node['edges']} edges{file_info}")

    print("\n[2] SAMPLE GRAPHIFY AST CONTEXT FED INTO QWEN CODE ANALYSIS:")
    sample_files = ["backend/pipeline.py", "backend/main.py"]
    context = get_graph_context_for_files(sample_files)
    for line in context.splitlines()[:18]:
        print(f"  {line}")

    print("\n" + "=" * 70)
    print("DEMONSTRATION COMPLETE: Graphify is successfully integrated and powering")
    print("Qwen Code Analysis with deterministic AST relationships.")
    print("=" * 70)

if __name__ == "__main__":
    main()
