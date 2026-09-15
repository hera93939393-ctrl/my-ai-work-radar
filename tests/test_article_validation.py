import ast
import unittest
from pathlib import Path


def load_validation_namespace():
    source_path = Path(__file__).resolve().parents[1] / "nodes.py"
    tree = ast.parse(source_path.read_text(encoding="utf-8"))

    selected_nodes = []
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if any(isinstance(target, ast.Name) and target.id == "REQUIRED_FIELDS" for target in targets):
                selected_nodes.append(node)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "code_validate_article":
            selected_nodes.append(node)

    namespace = {}
    module = ast.fix_missing_locations(ast.Module(body=selected_nodes, type_ignores=[]))
    exec(compile(module, source_path, "exec"), namespace)
    return namespace


class ArticleValidationTests(unittest.TestCase):
    def test_complete_article_passes_code_validation(self):
        namespace = load_validation_namespace()
        article = {
            "korean_title": "제목",
            "what_happened": "핵심 사실",
            "why_important": "중요한 이유",
            "for_workers": "실무자 의미",
            "try_today": "오늘 적용할 것",
            "content": "검수할 원문",
            "url": "https://example.com/article",
        }

        result = namespace["code_validate_article"](article)

        self.assertEqual("PASS", result["result"])
        self.assertEqual([], result["problems"])

    def test_missing_newsletter_field_fails_code_validation(self):
        namespace = load_validation_namespace()
        article = {
            "korean_title": "제목",
            "what_happened": "핵심 사실",
            "why_important": "중요한 이유",
            "for_workers": "실무자 의미",
            "try_today": "",
            "content": "검수할 원문",
            "url": "https://example.com/article",
        }

        result = namespace["code_validate_article"](article)

        self.assertEqual("FAIL", result["result"])
        self.assertIn("필수 필드 누락: try_today", result["problems"])


if __name__ == "__main__":
    unittest.main()
