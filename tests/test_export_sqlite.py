import os, shutil, sqlite3, tempfile, unittest
from scripts.export import load_all, export_sqlite

class TestSqlite(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_sqlite_tables_and_query(self):
        recs = load_all("data")
        recs[0]["是否发现"] = "否"
        db = export_sqlite(recs, os.path.join(self.tmp, "plants.sqlite"))
        con = sqlite3.connect(db)
        row = con.execute("SELECT 中文名, 科 FROM plant WHERE 学名 LIKE 'Ailanthus altissima%'").fetchone()
        self.assertEqual(row[0], "臭椿")
        self.assertIn("苦木科", row[1])
        columns = [r[1] for r in con.execute("PRAGMA table_info(plant)").fetchall()]
        self.assertIn("是否发现", columns)
        n = con.execute("SELECT COUNT(*) FROM synonym WHERE 学名 LIKE 'Ailanthus altissima%'").fetchone()[0]
        self.assertGreaterEqual(n, 1)
        con.close()

if __name__ == "__main__":
    unittest.main()
