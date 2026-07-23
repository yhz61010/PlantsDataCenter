import unittest

from scripts.retrieve_context import extract_terms, format_prompt, interested_fields, retrieve


RECORDS = [
    {
        "学名": "Ailanthus altissima (Mill.) Swingle",
        "中文名": "臭椿",
        "俗名": ["樗"],
        "异名": "无",
        "描述": "落叶乔木。",
        "分类系统": {"科": "Simaroubaceae-苦木科(kǔ mù kē)", "属": "Ailanthus-臭椿属(chòu chūn shǔ)"},
        "形态特征": {"叶": "奇数羽状复叶", "花": "圆锥花序"},
        "生态习性": {"分布": "华北常见"},
        "功用价值": {"观赏": "可作行道树"},
        "物种保护": "暂无数据",
        "分类信息": "暂无数据",
        "植物志": "暂无数据",
        "元数据": {"来源文件": "KM-苦木科.xlsx", "来源工作表": "臭椿"},
    },
    {
        "学名": "Magnolia denudata Desr.",
        "中文名": "玉兰",
        "俗名": "无",
        "异名": "无",
        "描述": "落叶乔木，花白色。",
        "分类系统": {"科": "Magnoliaceae-木兰科(mù lán kē)", "属": "Yulania-玉兰属(yù lán shǔ)"},
        "形态特征": {"花": "先叶开放"},
        "生态习性": "暂无数据",
        "功用价值": {"观赏": "庭园树种"},
        "物种保护": "暂无数据",
        "分类信息": "暂无数据",
        "植物志": "暂无数据",
        "元数据": {"来源文件": "ML-木兰科.xlsx", "来源工作表": "玉兰"},
    },
]


class TestRetrieveContext(unittest.TestCase):
    def test_extract_terms_generates_chinese_substrings(self):
        terms = extract_terms("臭椿有什么形态特征")
        self.assertIn("臭椿", terms)
        self.assertNotIn("形态", terms)
        self.assertNotIn("特征", terms)

    def test_retrieve_prioritizes_exact_chinese_name(self):
        hits = retrieve(RECORDS, "臭椿有什么形态特征和用途")
        self.assertGreaterEqual(len(hits), 1)
        self.assertEqual(hits[0]["record"]["中文名"], "臭椿")
        self.assertIn("中文名", hits[0]["matched_fields"])

    def test_retrieve_matches_taxonomy_question(self):
        hits = retrieve(RECORDS, "木兰科有哪些植物")
        self.assertEqual([hit["record"]["中文名"] for hit in hits], ["玉兰"])
        self.assertIn("分类系统", hits[0]["matched_fields"])

    def test_taxonomy_query_does_not_lock_to_common_name(self):
        records = RECORDS + [
            {
                "学名": "Yulania × soulangeana (Soul.-Bod.) D. L. Fu",
                "中文名": "二乔玉兰",
                "俗名": ["二乔木兰"],
                "异名": "无",
                "描述": "暂无数据",
                "分类系统": {"科": "Magnoliaceae-木兰科(mù lán kē)", "属": "Yulania-玉兰属(yù lán shǔ)"},
                "形态特征": "暂无数据",
                "生态习性": "暂无数据",
                "功用价值": "暂无数据",
                "物种保护": "暂无数据",
                "分类信息": "暂无数据",
                "植物志": "暂无数据",
                "元数据": {"来源文件": "ML-木兰科.xlsx", "来源工作表": "二乔玉兰"},
            }
        ]
        hits = retrieve(records, "木兰科有哪些植物")
        self.assertEqual([hit["record"]["中文名"] for hit in hits], ["二乔玉兰", "玉兰"])

    def test_belongs_to_question_keeps_species_context(self):
        records = RECORDS + [
            {
                "学名": "Yulania × soulangeana (Soul.-Bod.) D. L. Fu",
                "中文名": "二乔玉兰",
                "俗名": ["二乔木兰"],
                "异名": "无",
                "描述": "暂无数据",
                "分类系统": {"科": "Magnoliaceae-木兰科(mù lán kē)", "属": "Yulania-玉兰属(yù lán shǔ)"},
                "形态特征": "暂无数据",
                "生态习性": "暂无数据",
                "功用价值": "暂无数据",
                "物种保护": "暂无数据",
                "分类信息": "暂无数据",
                "植物志": "暂无数据",
                "元数据": {"来源文件": "ML-木兰科.xlsx", "来源工作表": "二乔玉兰"},
            }
        ]
        hits = retrieve(records, "玉兰属于什么科")
        self.assertEqual([hit["record"]["中文名"] for hit in hits], ["玉兰"])

    def test_interested_fields_detects_question_intent(self):
        fields = interested_fields("臭椿有什么形态特征和用途")
        self.assertIn("形态特征", fields)
        self.assertIn("功用价值", fields)

    def test_format_prompt_contains_grounding_instruction(self):
        hits = retrieve(RECORDS, "臭椿有什么用途")
        prompt = format_prompt(hits, "臭椿有什么用途")
        self.assertIn("请只根据下面资料回答问题", prompt)
        self.assertIn("臭椿", prompt)
        self.assertIn("功用价值", prompt)


if __name__ == "__main__":
    unittest.main()
