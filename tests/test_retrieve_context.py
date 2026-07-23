import unittest

from scripts.retrieve_context import (
    default_limit,
    extract_terms,
    format_context,
    format_prompt,
    interested_fields,
    retrieve,
    taxonomy_terms,
)


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
    {
        "学名": "Ulmus pumila L.",
        "中文名": "榆",
        "俗名": "无",
        "异名": "无",
        "描述": "落叶乔木。",
        "分类系统": {"科": "Ulmaceae-榆科(yú kē)", "属": "Ulmus-榆属(yú shǔ)"},
        "形态特征": {"叶": "叶缘具锯齿"},
        "生态习性": "暂无数据",
        "功用价值": "暂无数据",
        "物种保护": "暂无数据",
        "分类信息": "暂无数据",
        "植物志": "暂无数据",
        "元数据": {"来源文件": "Y-榆科.xlsx", "来源工作表": "榆"},
    },
    {
        "学名": "Artemisia argyi H. Lév. & Vaniot",
        "中文名": "艾",
        "俗名": "无",
        "异名": "无",
        "描述": "多年生草本。",
        "分类系统": {"科": "Asteraceae-菊科(jú kē)", "属": "Artemisia-蒿属(hāo shǔ)"},
        "形态特征": {"叶": "羽状深裂"},
        "生态习性": "暂无数据",
        "功用价值": {"经济价值": "全草入药"},
        "物种保护": "暂无数据",
        "分类信息": "暂无数据",
        "植物志": "暂无数据",
        "元数据": {"来源文件": "J-菊科.xlsx", "来源工作表": "艾"},
    },
]


class TestRetrieveContext(unittest.TestCase):
    def test_extract_terms_generates_chinese_substrings(self):
        terms = extract_terms("臭椿有什么形态特征")
        self.assertIn("臭椿", terms)
        self.assertNotIn("形态", terms)
        self.assertNotIn("特征", terms)

    def test_rank_terms_must_exist_in_taxonomy_vocab(self):
        vocab = taxonomy_terms(RECORDS)
        self.assertEqual(extract_terms("木兰科有哪些植物", rank_vocab=vocab), {"木兰科"})
        self.assertNotIn("项目", extract_terms("项目里的观赏树", rank_vocab=vocab))
        self.assertNotIn("门学科", extract_terms("这门学科怎么分类", rank_vocab=vocab))
        self.assertNotIn("臭椿的科", extract_terms("臭椿的科学分类", rank_vocab=vocab))

    def test_retrieve_prioritizes_exact_chinese_name(self):
        hits = retrieve(RECORDS, "臭椿有什么形态特征和用途")
        self.assertGreaterEqual(len(hits), 1)
        self.assertEqual(hits[0]["record"]["中文名"], "臭椿")
        self.assertIn("中文名", hits[0]["matched_fields"])
        self.assertNotIn("元数据", hits[0]["matched_fields"])

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

    def test_taxonomy_list_query_default_limit_is_unbounded(self):
        records = [
            {
                "学名": f"Rosa test{i}",
                "中文名": f"蔷薇测试{i}",
                "俗名": "无",
                "异名": "无",
                "描述": "暂无数据",
                "分类系统": {"科": "Rosaceae-蔷薇科(qiáng wēi kē)", "属": "Rosa-蔷薇属"},
                "形态特征": "暂无数据",
                "生态习性": "暂无数据",
                "功用价值": "暂无数据",
                "物种保护": "暂无数据",
                "分类信息": "暂无数据",
                "植物志": "暂无数据",
                "元数据": {"来源文件": "QW-蔷薇科.xlsx", "来源工作表": f"蔷薇测试{i}"},
            }
            for i in range(6)
        ]
        self.assertIsNone(default_limit(records, "蔷薇科植物有哪些？"))
        self.assertEqual(len(retrieve(records, "蔷薇科植物有哪些？", limit=default_limit(records, "蔷薇科植物有哪些？"))), 6)

        all_hits = retrieve(records, "蔷薇科植物有哪些？", limit=None)
        context = format_context(all_hits[:5], "蔷薇科植物有哪些？", total=len(all_hits))
        self.assertIn("总命中记录：6", context)
        self.assertIn("显示记录：5", context)

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

    def test_common_words_do_not_become_rank_queries(self):
        self.assertCountEqual([hit["record"]["中文名"] for hit in retrieve(RECORDS, "项目里的观赏树")], ["臭椿", "玉兰"])
        self.assertEqual([hit["record"]["中文名"] for hit in retrieve(RECORDS, "臭椿的科学分类")], ["臭椿"])

    def test_single_character_names_do_not_hard_lock_substrings(self):
        self.assertEqual(retrieve(RECORDS, "艾滋病"), [])
        self.assertEqual(retrieve(RECORDS, "桑拿"), [])
        self.assertEqual(retrieve(RECORDS, "构造"), [])
        self.assertEqual([hit["record"]["中文名"] for hit in retrieve(RECORDS, "艾")], ["艾"])

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
