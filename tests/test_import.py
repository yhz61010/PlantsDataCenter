import os, shutil, tempfile, unittest
import yaml
from scripts.import_xlsx import import_file, family_dir

class TestImport(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_family_dir_from_filename(self):
        self.assertEqual(family_dir("knowledge/KM-苦木科.xlsx"), "苦木科")
        self.assertEqual(family_dir("knowledge/MX-木樨科.xlsx"), "木樨科")

    def test_import_writes_yaml_that_roundtrips(self):
        paths = import_file("knowledge/KM-苦木科.xlsx", out_root=self.tmp)
        self.assertEqual(len(paths), 1)
        p = paths[0]
        self.assertTrue(p.endswith(os.path.join("苦木科", "臭椿.yaml")))
        with open(p, encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
        self.assertEqual(data["中文名"], "臭椿")
        self.assertEqual(data["分类系统"]["属"], "Ailanthus-臭椿属(chòu chūn shǔ)")
        self.assertEqual(data["元数据"]["来源工作表"], "臭椿")

    def test_all_fields_present_with_placeholders(self):
        paths = import_file("knowledge/KM-苦木科.xlsx", out_root=self.tmp)
        with open(paths[0], encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
        self.assertEqual(data["功用价值"], "暂无数据")
        self.assertEqual(data["物种保护"], "暂无数据")
        self.assertEqual(
            list(data.keys())[:5], ["学名","中文名","俗名","异名","描述"])

    def test_yaml_is_unicode_not_escaped(self):
        paths = import_file("knowledge/KM-苦木科.xlsx", out_root=self.tmp)
        with open(paths[0], encoding="utf-8") as fh:
            text = fh.read()
        self.assertIn("臭椿", text)
        self.assertNotIn("\\u", text)

if __name__ == "__main__":
    unittest.main()
