MATCH (u:User {userId: "duc.nguyenquang"})<-[:BOUGHT_BY]-(mor:Order)<-[:IN_ORDER]-(mit:Item)-[:IN_ORDER]->(oor:Order)-[:BOUGHT_BY]->(o:User)
MATCH (o)<-[:BOUGHT_BY]-(:Order)<-[:IN_ORDER]-(it:Item)
WHERE NOT EXISTS( (u)<-[:BOUGHT_BY]-(:Order)<-[:IN_ORDER]-(it) )
WITH u, o, mor, oor,  mit, it, COUNT(o) AS co ORDER BY co DESC
OPTIONAL MATCH (:User)<-[rv:REVIEWED_BY]-(it)
RETURN u, o, mor, oor, mit, it, COUNT(rv)
LIMIT 50