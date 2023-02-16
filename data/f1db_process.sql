# DON'T FORGET TO RUN f1db.sql FIRST!

USE formula1;

# Fix points bug in 1956 Argentine GP: resultID 18883 shows 5 points (Luigi Musso), but correct value is 4 points
update results
	set points = 4
	where resultId = 18883
;

# Fix position bug in 2019 Japanese GP: resultId 24542 shows position 16 (Robert Kubica), but correct position is 17
update results
	set position = 17
	where resultId = 24542
;