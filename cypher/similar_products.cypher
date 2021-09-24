MATCH (u:User {userId: "duc.nguyenquang"})<-[:BOUGHT_BY]-(:Order)<-[:IN_ORDER]-(it:Item)
MATCH (it)<-[:HAS]-(cat:Category)-[:HAS]->(oit:Item)
WHERE NOT EXISTS( (u)<-[:BOUGHT_BY]-(:Order)<-[:IN_ORDER]-(oit) )
WITH u, it, oit, cat, COUNT(*) AS cs 
OPTIONAL MATCH (:User)<-[rv:REVIEWED_BY]-(oit) 
WITH u, it, oit, cat, COUNT(rv) as crv, cs 
RETURN u, it, oit, cat, crv ORDER BY cs 
LIMIT 50