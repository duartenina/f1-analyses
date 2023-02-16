USE formula1;

select * from results where points > 0 order by resultId;
select * from results order by fastestLapSpeed DESC limit 25;
select * from races where raceId = 104;
select count(distinct raceId) from races;
select distinct year from races;
select * from results join races using (raceId) where points > 0 order by `year`;
select * from results where `rank` = 1 order by raceId;
select * from results join races using (raceId) where `rank` = 1 order by raceId;
select * from results
	join races using (raceId)
	join constructors using (constructorId)
	join drivers using (driverId)
	where `rank` = 1
	order by `year`;
select `year`, round, races.name, circuits.circuitRef, drivers.forename, drivers.surname, constructors.name, constructors.constructorRef, fastestLapTime, fastestLapSpeed from results
	join races using (raceId)
	join constructors using (constructorId)
	join drivers using (driverId)
    join circuits using (circuitId)
	where results.rank = 1
	order by `year`;
    
select resultId
	, `year`
    , round
    , races.name
    , circuits.circuitRef
    , drivers.forename
    , drivers.surname
    , constructors.name
    , constructors.constructorRef
from results
	join races using (raceId)
	join constructors using (constructorId)
	join drivers using (driverId)
    join circuits using (circuitId)
where results.position = 1
order by `year`;

select * from qualifying;
select * from qualifying join races using (raceId) join circuits using (circuitId) order by `year`;
select raceId
	, `year`
    , round
    , races.name
    , circuits.circuitRef
    , drivers.forename
    , drivers.surname
    , constructors.name
    , constructors.constructorRef
from qualifying
	join races using (raceId)
	join constructors using (constructorId)
	join drivers using (driverId)
    join circuits using (circuitId)
where qualifying.position = 1
order by `year`;

select * from drivers;

select resultId, raceId, constructorId, driverId, points from results where points > 0;
select resultId, raceId, constructorId, driverId, sum(points) as sp from results group by raceId, constructorId;
select r1.raceId
	, `year`
    , round
    , races.name
    , circuits.circuitRef
    , drivers.forename
    , drivers.surname
    , constructors.name
    , constructors.constructorRef
	from (select resultId, raceId, constructorId, driverId, sum(points) as sp from results group by raceId, constructorId) as r1
		join races using (raceId)
		join constructors using (constructorId)
		join drivers using (driverId)
		join circuits using (circuitId)
    inner join (
		select constructorId, raceId, max(sp) as sp
        from (select raceId, constructorId, sum(points) as sp from results group by raceId, constructorId) as rt
        group by raceId
        #order by sp
    ) as r2
    on (r1.raceId = r2.raceId and r1.sp = r2.sp and r1.constructorId = r2.constructorId)
    order by `year`;
    #order by r1.raceId;
select raceId, constructorId, max(sp) as sp
	from (select raceId, constructorId, sum(points) as sp from results group by raceId, constructorId) as rt
	group by raceId;
    
select * from constructorStandings where position=1;
select constructorStandingsId
	, `year`
    , round
    , races.name
    , circuits.circuitRef
    #, drivers.forename
    #, drivers.surname
    , constructors.name
    , constructors.constructorRef
from constructorStandings
	join races using (raceId)
	join constructors using (constructorId)
	#join drivers using (driverId)
    join circuits using (circuitId)
where constructorStandings.position = 1
order by `year`;

select r1.raceId#, r1.constructorId, r1.sp
	, `year`
    , round
    , races.name
    , circuits.circuitRef
    , drivers.forename
    , drivers.surname
    , constructors.name
    , constructors.constructorRef
	from driverStandings as r1
		join races using (raceId)
		join constructors using (constructorId)
		join drivers using (driverId)
		join circuits using (circuitId)
    inner join (
		select `year`, as sp
        from driverStandings as rt
			join races using raceId
        group by `year`
        order by round
    ) as r2
    on (r1.raceId = r2.raceId and r1.sp = r2.sp)# and r1.resultId = r2.resultId)
    order by `year`;
    #order by r1.raceId;

select * from driverStandings;
select `year`
		, driverStandingsId
		, round
		, drivers.forename
		, drivers.surname
		, constructors.name
		, constructors.constructorRef
		, driverStandings.points
	from driverStandings
		join races using (raceId)
		join results using (raceId, driverId)
		join constructors using (constructorId)
		join drivers using (driverId)
	where (driverStandings.position = 1)
	order by `year` desc, round DESC
;
select `year`, round, driverStandingsId
	from driverStandings join races using (raceId)
	where (driverStandings.position = 1) order by `year`, round desc;

# WDCs    
select mround.`year`, driverId
	from (select `year`, max(round) as finalRound from races group by `year` order by `year`) as mround
		inner join races on (races.`year` = mround.`year` and races.round = mround.finalRound)
		join driverStandings using (raceId)
	where driverStandings.position = 1
	order by mround.year;

# WCCs    
select mround.`year` as `year`, constructorId
	from (select `year`, max(round) as finalRound from races group by `year` order by `year`) as mround
		inner join races on (races.`year` = mround.`year` and races.round = mround.finalRound)
		join constructorStandings using (raceId)
	where constructorStandings.position = 1
	order by mround.year;

# Most wins
select * from drivers;
select driverId, driverRef, surname, count(*) as wins from results
	join drivers using (driverId)
    where position = 1
	group by driverId
    order by wins desc;
    
SELECT DISTINCT `year`
	FROM results
	JOIN constructors USING (constructorId)
	JOIN races USING (raceId)
	WHERE constructorRef = 'mercedes'	
;

#### find num wins per team per year
SELECT `constructorRef`, `year`, COUNT(*) AS `wins`
	FROM results
	JOIN constructors USING (constructorId)
	JOIN races USING (raceId)	
	WHERE `position` = 1
	GROUP BY `constructorRef`, `year`
	ORDER BY `year` DESC, `wins` DESC 
;

#### find team with most wins per year
SELECT t.`year`, t.`constructorRef`, MAX(t.`wins`) as `max_wins`
	FROM (
		SELECT `constructorRef`, `year`, COUNT(*) AS `wins`
			FROM results
			JOIN constructors USING (constructorId)
			JOIN races USING (raceId)	
			WHERE `position` = 1
			GROUP BY `constructorRef`, `year`
			ORDER BY `year` DESC, `wins` DESC 
	) AS t
	GROUP BY `year`
	ORDER BY `year` DESC 
;
SELECT t_wins.`year`, t_wins.`constructorRef`, t_wins.`wins`
	FROM (
		SELECT `constructorRef`, `year`, COUNT(*) AS `wins`
			FROM results
			JOIN constructors USING (constructorId)
			JOIN races USING (raceId)	
			WHERE `position` = 1
			GROUP BY `constructorRef`, `year`
	) t_wins
	JOIN (
		SELECT t.`year`, MAX(t.`wins`) as `max_wins`
			FROM (
				SELECT `constructorRef`, `year`, COUNT(*) AS `wins`
					FROM results
					JOIN constructors USING (constructorId)
					JOIN races USING (raceId)	
					WHERE `position` = 1
					GROUP BY `constructorRef`, `year`
			) t
			GROUP BY `year`
	) t_max_wins
	ON ((t_wins.`year` = t_max_wins.`year`) AND (t_wins.`wins` = t_max_wins.`max_wins`))		# returns all teams with wins = max_wins
	ORDER BY `year` DESC
;

#### find driver with most wins per year
SELECT t.`year`, t.`driverRef`, MAX(t.`wins`) as `max_wins`
	FROM (
		SELECT `driverRef`, `year`, COUNT(*) AS `wins`
			FROM results
			JOIN drivers USING (driverId)
			JOIN races USING (raceId)	
			WHERE `position` = 1
			GROUP BY `driverRef`, `year`
			ORDER BY `year` DESC, `wins` DESC 
	) AS t
	GROUP BY `year`
	ORDER BY `year` DESC 
;

# count duplicate results
select raceId, position, count(*)
	from results
	where position is not null
	group by raceId, position
	having count(*) > 1
;

# find duplicate results (multiple drivers in the same car)
select resultId,
		raceId, `year`, round, races.name,
		driverId, driverRef,
		constructorId, constructorRef,
		grid, r.position, positionOrder,
		r.points, ds.points as total_points,
		laps, r.`time`, statusId
	from (
		select a.*
		from results a
		join (
			select raceId, position
				from results
				where position is not null
				group by raceId, position
				having count(*) > 1 #and position = 1
		) b
		on a.raceId = b.raceId and a.position = b.position
	) r
	join drivers using (driverId)
	join constructors using (constructorId)
	join races using (raceId)
	join driverstandings ds using (raceId, driverId)
	where races.name <> "Indianapolis 500"
	order by year , round , positionOrder
;