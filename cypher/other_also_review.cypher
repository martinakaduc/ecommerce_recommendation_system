MATCH (u:User {userId: "duc.nguyenquang"})<-[rv:REVIEWED_BY]-(mit:Item)-[:REVIEWED_BY]->(o:User)
WITH u, mit, o, avg(rv.overall) AS mean
MATCH (o)<-[r:REVIEWED_BY]-(it:Item)
WHERE NOT EXISTS( (u)<-[:REVIEWED_BY]-(it) )
AND NOT EXISTS( (u)<-[:BOUGHT_BY]-(:Order)<-[:IN_ORDER]-(it) )
AND r.overall >= mean
WITH u, o, mit, it, COUNT(o) AS co ORDER BY co DESC
OPTIONAL MATCH (:User)<-[rv:REVIEWED_BY]-(it)
RETURN u, o, mit, it, COUNT(rv)
LIMIT 50