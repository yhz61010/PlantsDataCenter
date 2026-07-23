import json, os, shutil, tempfile, unittest
from scripts.export import load_all, export_json, to_markdown

class TestExport(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_load_all_reads_records(self):
        recs = load_all("data")
        self.assertTrue(any(r["中文名"] == "臭椿" for r in recs))

    def test_export_json_valid_and_unicode(self):
        recs = load_all("data")
        out = export_json(recs, os.path.join(self.tmp, "plants.json"))
        with open(out, encoding="utf-8") as fh:
            data = json.load(fh)
        self.assertEqual(data[0]["中文名"], sorted(r["中文名"] for r in recs)[0])
        with open(out, encoding="utf-8") as fh:
            raw = fh.read()
        self.assertIn("臭椿", raw)          # ensure_ascii=False

    def test_markdown_has_frontmatter_body_and_skips_placeholders(self):
        rec = {"学名": "Ailanthus altissima (Mill.) Swingle", "中文名": "臭椿",
               "描述": "落叶乔木。", "分类系统": {"科": "Simaroubaceae-苦木科(kǔ mù kē)"},
               "形态特征": {"叶": "羽状复叶"}, "功用价值": "暂无数据",
               "植物志": "20. 臭椿……"}
        md = to_markdown(rec)
        self.assertTrue(md.startswith("---\n"))
        self.assertIn("学名:", md)
        self.assertIn("# 臭椿", md)
        self.assertIn("## 形态特征", md)
        self.assertIn("羽状复叶", md)
        self.assertIn("## 植物志", md)
        self.assertNotIn("## 功用价值", md)   # 占位区块不渲染

if __name__ == "__main__":
    unittest.main()
