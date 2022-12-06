-- 将存储语料旧表改为新表
ALTER TABLE corpus RENAME TO tableOld;
CREATE TABLE IF NOT EXISTS Corpus_2(id INTEGER PRIMARY KEY AUTOINCREMENT,simple BLOB NOT NULL,used INTEGER default 0,UNIQUE(simple));
CREATE UNIQUE INDEX IF NOT EXISTS Corpus_2_simple_index on Corpus_2(simple);
INSERT Or IGNORE INTO Corpus_2(simple) SELECT Content as simple FROM tableOld;
SELECT COUNT(*) FROM Corpus_2;
SELECT COUNT(*) FROM  tableOld;
drop table tableOld;


-- 重置数据，将数据库恢复到初始状态，重新开始运行
UPDATE Corpus_2 SET used=0 WHERE used=1;  -- 将所有预料这是为未使用
DROP TABLE OriginalTestcases;
DROP TABLE Testcases;
DROP TABLE Engines;
DROP TABLE Outputs;
DROP TABLE DifferentialTestResults;
-- 有必要时，记得删除过滤数据库表