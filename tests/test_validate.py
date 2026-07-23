import unittest
from scripts.validate import validate_record

GOOD = {
    "学名": "Ailanthus altissima (Mill.) Swingle",
    "中文名": "臭椿",
    "俗名": ["樗"],
    "异名": "无",
    "描述": "暂无数据",
    "分类系统": {
        "界": "Plantae-植物界(zhí wù jiè)",
        "门": "Tracheophyta-维管植物门(wéi guǎn zhí wù mén)",
        "纲": "Magnoliopsida-木兰纲(mù lán gāng)",
        "目": "Sapindales-无患子目(wú huàn zǐ mù)",
        "科": "Simaroubaceae-苦木科(kǔ mù kē)",
        "属": "Ailanthus-臭椿属(chòu chūn shǔ)",
    },
    "物种保护": "暂无数据",
    "分类信息": "暂无数据",
    "形态特征": {"生活型": "落叶乔木"},
    "生态习性": "暂无数据",
    "功用价值": "暂无数据",
    "植物志": "暂无数据",
    "元数据": {"来源文件": "KM-苦木科.xlsx", "来源工作表": "臭椿"},
}

class TestValidate(unittest.TestCase):
    def test_good_record_with_placeholders_passes(self):
        self.assertEqual(validate_record(GOOD, "data/苦木科/臭椿.yaml"), [])

    def test_missing_field_reported(self):
        bad = dict(GOOD); del bad["功用价值"]
        errs = validate_record(bad, "data/苦木科/臭椿.yaml")
        self.assertTrue(any("功用价值" in e for e in errs))

    def test_scientific_name_must_be_real(self):
        bad = dict(GOOD); bad["学名"] = "暂无数据"
        errs = validate_record(bad, "data/苦木科/臭椿.yaml")
        self.assertTrue(any("学名" in e for e in errs))

    def test_bad_taxonomy_format(self):
        bad = dict(GOOD)
        bad["分类系统"] = dict(GOOD["分类系统"], 属="臭椿属")   # 缺拉丁名与拼音
        errs = validate_record(bad, "data/苦木科/臭椿.yaml")
        self.assertTrue(any("属" in e for e in errs))

    def test_taxonomy_placeholder_ok(self):
        ok = dict(GOOD); ok["分类系统"] = "暂无数据"
        self.assertEqual(validate_record(ok, "data/苦木科/臭椿.yaml"), [])

    def test_hybrid_scientific_name_ok(self):
        # 杂交种名带 × 记号是合法二名法，不应报错。
        ok = dict(GOOD); ok["学名"] = "Yulania × soulangeana (Soul.-Bod.) D. L. Fu"
        ok["中文名"] = "二乔玉兰"
        self.assertEqual(validate_record(ok, "data/木兰科/二乔玉兰.yaml"), [])

    def test_taxonomy_without_pinyin_ok(self):
        # 个别源数据分类阶缺拼音（如 'Ericales-杜鹃花目'），拼音可选，应放行。
        ok = dict(GOOD)
        ok["分类系统"] = dict(GOOD["分类系统"], 目="Ericales-杜鹃花目")
        self.assertEqual(validate_record(ok, "data/苦木科/臭椿.yaml"), [])

    def test_common_name_list_or_placeholder(self):
        bad = dict(GOOD); bad["俗名"] = 123
        errs = validate_record(bad, "data/苦木科/臭椿.yaml")
        self.assertTrue(any("俗名" in e for e in errs))

    def test_filename_must_match_chinese_name(self):
        errs = validate_record(GOOD, "data/苦木科/错误名.yaml")
        self.assertTrue(any("文件名" in e for e in errs))

if __name__ == "__main__":
    unittest.main()
