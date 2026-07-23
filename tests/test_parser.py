import os
import unittest
from scripts.xlsx_reader import read_sheets
from scripts.parser import parse_species

def load(path, sheet):
    for name, rows in read_sheets(path):
        if name == sheet:
            return parse_species(rows, os.path.basename(path), name)
    raise AssertionError(f"未找到工作表 {sheet}")

class TestParser(unittest.TestCase):
    def test_km_scalars_desc_and_field_order(self):
        r = load("knowledge/KM-苦木科.xlsx", "臭椿")
        self.assertEqual(r["学名"], "Ailanthus altissima (Mill.) Swingle")
        self.assertEqual(r["中文名"], "臭椿")
        self.assertEqual(len(r["俗名"]), 9)
        self.assertEqual(len(r["异名"]), 6)
        self.assertTrue(r["描述"].startswith("落叶乔木，高可达20米"))
        self.assertEqual(
            list(r.keys())[:13],
            ["学名","中文名","俗名","异名","描述","分类系统","物种保护",
             "分类信息","形态特征","生态习性","功用价值","植物志","元数据"],
        )

    def test_km_taxonomy_and_morphology(self):
        r = load("knowledge/KM-苦木科.xlsx", "臭椿")
        self.assertEqual(r["分类系统"]["科"], "Simaroubaceae-苦木科(kǔ mù kē)")
        self.assertEqual(list(r["分类系统"].keys()), ["界","门","纲","目","科","属"])
        self.assertEqual(r["形态特征"]["生活型"], "落叶乔木")
        self.assertEqual(r["形态特征"]["叶"][:6], "奇数羽状复叶")
        self.assertNotIn("：", "".join(r["形态特征"].keys()))

    def test_km_synonym_marker_stripped(self):
        r = load("knowledge/KM-苦木科.xlsx", "臭椿")
        self.assertEqual(r["异名"][0], "Toxicodendron altissimum")
        self.assertNotIn("synonym", "".join(r["异名"]))

    def test_km_missing_sections_get_placeholder(self):
        r = load("knowledge/KM-苦木科.xlsx", "臭椿")
        self.assertEqual(r["物种保护"], "暂无数据")
        self.assertEqual(r["分类信息"], "暂无数据")
        self.assertEqual(r["功用价值"], "暂无数据")
        self.assertEqual(r["生态习性"]["物候"], "花期4-5月，果期8-10月")
        self.assertTrue(r["植物志"].startswith("本种在石灰岩地区"))   # 尾部无标签文本

    def test_hua_full_sections_and_flora(self):
        r = load("knowledge/D-豆科.xlsx", "槐")
        self.assertEqual(r["分类信息"]["模式产地"], "模式标本采自四川成都附近")
        self.assertEqual(r["功用价值"]["经济价值"][:4], "树冠优美")
        self.assertTrue(r["植物志"].startswith("20. 槐"))
        self.assertIn("下级分类", r["植物志"])

    def test_baihe_missing_desc_and_protection(self):
        r = load("knowledge/BH-百合科.xlsx", "百合")
        self.assertEqual(r["描述"], "暂无数据")           # 百合无概述段
        self.assertEqual(r["物种保护"]["濒危等级"], "无")
        self.assertEqual(r["异名"][0], "Lilium odorum")

    def test_metadata(self):
        r = load("knowledge/KM-苦木科.xlsx", "臭椿")
        self.assertEqual(r["元数据"]["来源文件"], "KM-苦木科.xlsx")
        self.assertEqual(r["元数据"]["来源工作表"], "臭椿")

    def test_zijing_continuation_and_stray_paragraph(self):
        # 紫荆：功用价值.植物文化 是一首诗，续行（C-only）应拼进该子键而非植物志；
        # 该物种无尾部植物志；行尾一段无标签 B-only 段落应进 备注（不丢弃）。
        r = load("knowledge/D-豆科.xlsx", "紫荆")
        self.assertIn("杜甫", r["功用价值"]["植物文化"])     # 诗尾署名并入子键
        self.assertEqual(r["植物志"], "暂无数据")            # 诗未被误当植物志
        self.assertIn("木本花卉", r.get("备注", ""))         # 游离段落被保留

    def test_jishutiao_taxonomy_footnote_to_notes(self):
        # 鸡树条：分类系统内（科与属之间）插入的脚注属原子分类阶之外，应进 备注，
        # 不得污染分类阶值，也不得被当作植物志。
        r = load("knowledge/JM-荚蒾科.xlsx", "鸡树条")
        self.assertEqual(r["植物志"], "暂无数据")
        self.assertIn("五福花科", r.get("备注", ""))
        self.assertEqual(r["分类系统"]["科"], "Viburnaceae-荚蒾科(jiá mí kē)")

    def test_yulan_contiguous_poem_stays_in_subkey(self):
        # 玉兰：植物文化《题玉兰》的诗行与子键“紧接无空行”，应续接进 植物文化，
        # 不得因“其后无 B 行”而漏进植物志（空行间隔才是植物志信号）。
        r = load("knowledge/ML-木兰科.xlsx", "玉兰")
        self.assertIn("沈周", r["功用价值"]["植物文化"])
        self.assertIn("霓裳", r["功用价值"]["植物文化"])
        self.assertNotIn("霓裳", r["植物志"])

    def test_jinzhonghua_chinese_note_not_synonym_and_image_caption(self):
        # 金钟花：异名段里混入中文说明（无 (synonym) 标记），不得当作异名，应进 备注；
        # 真正的拉丁异名仍保留；尾部“下图是…图片”是图片说明，不得进入植物志。
        r = load("knowledge/MX-木樨科.xlsx", "金钟花")
        self.assertEqual(r["异名"], ["Rangium viridissimum"])
        self.assertIn("区别", r.get("备注", ""))
        self.assertEqual(r["植物志"], "暂无数据")
        self.assertIn("髓部图片", r.get("备注", ""))

    def test_lianqiao_comparison_table_not_dropped(self):
        # 连翘：异名段内嵌入“连翘 vs 金钟花”对比表（B/C 同行），
        # 其 C 值不得静默丢弃，应连同 B 标签进 备注。断言真正被抢救的表格 C 值
        # （旧代码会丢，故该断言对旧代码为假、对新代码为真）。
        r = load("knowledge/MX-木樨科.xlsx", "连翘")
        self.assertIn("原生种", r.get("备注", ""))            # 表格 C 值被保留
        self.assertIn("枝条中心是空的", r.get("备注", ""))     # 另一表格 C 值
        self.assertTrue(r["植物志"].startswith("1. 连翘"))    # 真正的植物志仍保留

    def test_shukui_stray_field_value_preserved(self):
        # 蜀葵：异名段内一行“模式产地/原产四川”（B+C），C 值须保留进 备注（旧代码只留 B 标签）。
        r = load("knowledge/JK-锦葵科.xlsx", "蜀葵")
        self.assertIn("原产四川", r.get("备注", ""))

if __name__ == "__main__":
    unittest.main()
