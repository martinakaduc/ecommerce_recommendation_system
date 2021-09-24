MATCH (me:User {userId: "duc.nguyenquang"})<-[rvm:REVIEWED_BY]-(it:Item)
WITH me, gds.alpha.similarity.asVector(it, rvm.overall) AS meVector
MATCH (you:User)<-[rvy:REVIEWED_BY]-(it) WHERE you <> me

WITH me, you, meVector, gds.alpha.similarity.asVector(it, rvy.overall) AS youVector
WHERE size(apoc.coll.intersection([v in meVector | v.category], [v in youVector | v.category])) > 9

WITH me, you, gds.alpha.similarity.pearson(meVector, youVector, {vectorType: "maps"}) AS similarity 
ORDER BY similarity DESC LIMIT 10

MATCH (you)<-[r:REVIEWED_BY]-(it:Item)
WHERE NOT EXISTS( (me)<-[:REVIEWED_BY]-(it) )
AND NOT EXISTS( (me)<-[:BOUGHT_BY]-(:Order)<-[:IN_ORDER]-(it) )
WITH me, you, it, similarity, SUM( similarity * r.overall ) AS score
ORDER BY score DESC LIMIT 50

MATCH (:User)<-[r:REVIEWED_BY]-(it)
RETURN me, you, similarity, it, COUNT(r), score