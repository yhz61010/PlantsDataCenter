import unittest
from scripts.xlsx_reader import col_letter, read_sheets

KM = "knowledge/KM-苦木科.xlsx"

class TestXlsxReader(unittest.TestCase):
    def test_col_letter(self):
        self.assertEqual(col_letter("A1"), "A")
        self.assertEqual(col_letter("C11"), "C")
        self.assertEqual(col_letter("AB123"), "AB")

    def test_read_sheets_skips_image_sheet_and_reads_grid(self):
        sheets = read_sheets(KM)
        names = [n for n, _ in sheets]
        self.assertEqual(names, ["臭椿"])            # 图片表已跳过（KM 无图片表，仍应只有臭椿）
        rows = dict((r["r"], r) for _, rows in sheets for r in rows)
        self.assertEqual(rows[1]["A"], "学名")
        self.assertEqual(rows[1]["B"], "Ailanthus altissima (Mill.) Swingle")
        self.assertEqual(rows[17]["C"], "Simaroubaceae-苦木科(kǔ mù kē)")
        self.assertEqual(rows[4]["B"], "Toxicodendron altissimum\xa0(synonym)")

if __name__ == "__main__":
    unittest.main()
