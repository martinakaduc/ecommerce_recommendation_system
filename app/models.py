from neomodel import *

class UserManagement():
    @classmethod
    def add(cls, username, name, password):
        new_idx = len(User.nodes)
        return User(index=new_idx, userId=username, name=name, password=password).save()

    @classmethod
    def verify(cls, username, password):
        return User.nodes.get_or_none(userId=username, password=password)

    @classmethod
    def get(cls, userId):
        return User.nodes.get_or_none(userId=userId)

class ItemManagement():
    @classmethod
    def get_all_items(cls, start, limit):
        results, meta = db.cypher_query("MATCH (n:Item) \
                                         OPTIONAL MATCH (:User)<-[rv:REVIEWED_BY]-(n) \
                                         RETURN n, COUNT(rv) AS crv \
                                         ORDER BY crv DESC \
                                         SKIP %d LIMIT %d" 
                                         % (start, limit))
        return [(Item.inflate(row[0]), row[1]) for row in results]

    @classmethod
    def get_number_items(cls, category_idx=None):
        if category_idx == None or (category_idx != None and category_idx < 0):
            return len(Item.nodes)
        else:
            results, meta = db.cypher_query("MATCH (n:Item)<-[:HAS]-(cat:Category {index: %d}) \
                                                RETURN COUNT(n)" 
                                                % (category_idx))
            return results[0][0]

    @classmethod
    def get_item_by_id(cls, id):
        return Item.nodes.get_or_none(itemId=id)

    @classmethod
    def get_item_by_keyword(cls, keyword, start=0, limit=24):
        results, meta = db.cypher_query("MATCH (n:Item) \
                                         WHERE n.title CONTAINS \"%s\" \
                                         WITH n \
                                         OPTIONAL MATCH (:User)<-[rv:REVIEWED_BY]-(n) \
                                         RETURN n, COUNT(rv) AS crv \
                                         ORDER BY crv DESC \
                                         SKIP %d LIMIT %d"
                                         % (keyword, start, limit))
        return [(Item.inflate(row[0]), row[1]) for row in results]
    
    @classmethod
    def count_item_by_keyword(cls, keyword):
        results, meta = db.cypher_query("MATCH (n:Item) \
                                         WHERE n.title CONTAINS \"%s\"\
                                         RETURN COUNT(n)"
                                         % (keyword))
        return results[0][0]

    @classmethod
    def get_products_by_category(cls, category_idx, start, limit):
        if category_idx != None and category_idx >= 0:
            results, meta = db.cypher_query("MATCH (n:Item)<-[:HAS]-(cat:Category {index: %d}) \
                                                OPTIONAL MATCH (:User)<-[rv:REVIEWED_BY]-(n) \
                                                RETURN n, COUNT(rv) AS crv \
                                                ORDER BY crv DESC \
                                                SKIP %d LIMIT %d" 
                                                % (category_idx, start, limit))
            return [(Item.inflate(row[0]), row[1]) for row in results]

    @classmethod
    def get_popular_products(cls, category, limit):
        if category != None:
            results, meta = db.cypher_query("MATCH (n:Item)<-[:HAS]-(cat:Category {index: %d}) \
                                            OPTIONAL MATCH (:Order)<-[io:IN_ORDER]-(n) \
                                            WITH n, COUNT(io) as cio ORDER BY cio DESC \
                                            OPTIONAL MATCH (:User)<-[rv:REVIEWED_BY]-(n) \
                                            RETURN n, cio, COUNT(rv) AS crv \
                                            ORDER BY cio DESC, crv DESC LIMIT %d" 
                                            % (category.index, limit))
            return [(Item.inflate(row[0]), row[2]) for row in results]

class CategoryManagement():
    root_category_idx = [0, 18, 35, 63, 78]

    @classmethod
    def get_root_categories(cls):
        root_categories = []
        for cat_idx in cls.root_category_idx:
            root_categories.append(Category.nodes.get_or_none(index=cat_idx))
        return root_categories

    @classmethod
    def get_category_by_id(cls, id):
        return Category.nodes.get_or_none(index=id)

class CartManagement():
    @classmethod
    def add_to_cart(cls, userId, itemId, quantity):
        user = UserManagement.get(userId)
        item = ItemManagement.get_item_by_id(itemId)

        if user == None or item == None:
            return False

        if item.price == None:
           return False
        else:
            subTotal = item.price * quantity

        if user.cart_items.is_connected(item):
            rel = user.cart_items.relationship(item)
            rel.price =  item.price
            rel.quantity += quantity
            rel.subTotal += subTotal
            rel.save()

        else:
            rel = user.cart_items.connect(item,
                    {'price': item.price, 'quantity': quantity, 'subTotal': subTotal})
            rel.save()

        return True

    @classmethod
    def update_whole_cart(cls, userId, item_quantity_dict):
        user = UserManagement.get(userId)
        user.cart_items.disconnect_all()

        for itemId, quantity in item_quantity_dict.items():
            item = ItemManagement.get_item_by_id(itemId)

            if item == None or quantity == "NaN":
                continue

            if item.price == None:
                subTotal = 0
            else:
                subTotal = item.price * float(quantity)

            rel = user.cart_items.connect(item,
                    {'price': item.price, 'quantity': quantity, 'subTotal': subTotal})
            rel.save()

        return True

    @classmethod
    def get_items_of_user(cls, userId):
        user = UserManagement.get(userId)

        definition = dict(node_class=Item, direction=match.INCOMING,
                  relation_type="IN_CART", model=Cart)

        items = Traversal(user, Item.__label__,
                                        definition)
        
        rels = []
        for item in items:
            rel = user.cart_items.relationship(item)
            rels.append(rel)

        return rels, items

    @classmethod
    def count_items(cls, userId):
        user = UserManagement.get(userId)
        definition = dict(node_class=Item, direction=match.INCOMING,
                  relation_type="IN_CART", model=Cart)

        items = Traversal(user, Item.__label__,
                                        definition)
        
        item_count = 0
        for item in items:
            rel = user.cart_items.relationship(item)
            item_count += int(rel.quantity)

        return item_count

    @classmethod
    def checkout(cls, userId, time):
        user = UserManagement.get(userId)

        definition = dict(node_class=Item, direction=match.INCOMING,
                  relation_type="IN_CART", model=Cart)

        items = Traversal(user, Item.__label__, definition)

        totalPrice = 0
        for item in items:
            cart_rel = user.cart_items.relationship(item)
            totalPrice += cart_rel.subTotal

        new_order = OrderManagement.create_new_order(time, totalPrice)
        user_order = user.owned_orders.connect(new_order)

        for item in items:
            cart_rel = user.cart_items.relationship(item)
            order_rel = new_order.items.connect(item, {"price": cart_rel.price,
                                                       "quantity": cart_rel.quantity,
                                                       "subTotal": cart_rel.subTotal})
            order_rel.save()

        user.cart_items.disconnect_all()
        return True
        
class OrderManagement():
    @classmethod
    def create_new_order(cls, time, totalPrice):
        new_idx = len(Order.nodes)
        return Order(index=new_idx, time=time, totalPrice=totalPrice).save()

    @classmethod
    def get_orders(cls, userId):
        user = UserManagement.get(userId)
        order_definition = dict(node_class=Order, direction=match.INCOMING,
                  relation_type="BOUGHT_BY", model=OrderOwner)

        orders = Traversal(user, Order.__label__, order_definition)
        list_order = {}
        order_details = {}
        list_items = {}

        item_definition = dict(node_class=Item, direction=match.INCOMING,
                  relation_type="IN_ORDER", model=OrderPartial)

        for order in orders:
            list_order[order.index] = order
            order_details[order.index] = {}
            items = Traversal(order, Item.__label__, item_definition)

            for item in items:
                if item.itemId not in list_items:
                    list_items[item.itemId] = item

                order_item = order.items.relationship(item)
                order_details[order.index][item.itemId] = order_item

        return list_order, order_details, list_items

    @classmethod
    def get_all_ordered_products(cls, userId):
        user = UserManagement.get(userId)
        order_definition = dict(node_class=Order, direction=match.INCOMING,
                  relation_type="BOUGHT_BY", model=OrderOwner)

        orders = Traversal(user, Order.__label__, order_definition)
        list_items = {}
        personal_reviews = {}

        item_definition = dict(node_class=Item, direction=match.INCOMING,
                  relation_type="IN_ORDER", model=OrderPartial)

        for order in orders:
            items = Traversal(order, Item.__label__, item_definition)

            for item in items:
                if item.itemId not in list_items:
                    list_items[item.itemId] = item
                    personal_reviews[item.itemId] = user.review_items.relationship(item)

        return list_items, personal_reviews

    @classmethod
    def is_bought(cls, userId, itemId):
        user = UserManagement.get(userId)
        order_definition = dict(node_class=Order, direction=match.INCOMING,
                  relation_type="BOUGHT_BY", model=OrderOwner)

        orders = Traversal(user, Order.__label__, order_definition)
        item_definition = dict(node_class=Item, direction=match.INCOMING,
                  relation_type="IN_ORDER", model=OrderPartial)

        for order in orders:
            items = Traversal(order, Item.__label__, item_definition)

            for item in items:
                if item.itemId == itemId:
                    return True
        
        return False

class ReviewManagement():
    @classmethod
    def create_review(cls, userId, itemId, overall, reviewText, reviewTime):
        user = UserManagement.get(userId)
        item = ItemManagement.get_item_by_id(itemId)

        if user == None or item == None:
            return False

        if user.review_items.is_connected(item):
            rel = user.review_items.relationship(item)
            rel.overall =  overall
            rel.reviewText = reviewText
            rel.reviewTime = reviewTime
            rel.save()

        else:
            rel = user.review_items.connect(item,
                    {'overall': overall, 'reviewText': reviewText, 'reviewTime': reviewTime})
            rel.save()

        item.reviewOverall = cls._get_avg_review_of_item(itemId)
        item.save()

        return True

    @classmethod
    def _get_avg_review_of_item(cls, itemId):
        results, meta = db.cypher_query("MATCH (:User)<-[rv:REVIEWED_BY]-(n:Item {itemId: \"%s\"}) \
                                         RETURN AVG(rv.overall)" 
                                         % (itemId))
        return results[0][0]

    @classmethod
    def get_reviews_of_item(cls, itemId, start=0, limit=24):
        results, meta = db.cypher_query("MATCH (u:User)<-[rv:REVIEWED_BY]-(n:Item {itemId: \"%s\"}) \
                                         RETURN u, rv \
                                         SKIP %d LIMIT %d" 
                                         % (itemId, start, limit))
        return [(User.inflate(row[0]), Review.inflate(row[1])) for row in results]

    @classmethod
    def get_reviews_of_user(cls, userId, start=0, limit=48):
        results, meta = db.cypher_query("MATCH (u:User {userId: \"%s\"})<-[rv:REVIEWED_BY]-(n:Item) \
                                         RETURN n, rv \
                                         SKIP %d LIMIT %d" 
                                         % (userId, start, limit))
        return [(Item.inflate(row[0]), Review.inflate(row[1])) for row in results]

class Recommendation():
    @classmethod
    def content_based(cls, userId, start=0, limit=24):
        results, meta = db.cypher_query("\
        MATCH (u:User {userId: \"%s\"})<-[:BOUGHT_BY]-(:Order)<-[:IN_ORDER]-(it:Item) \
        MATCH (it)<-[:HAS]-(:Category)-[:HAS]->(oit:Item) \
        WHERE NOT EXISTS( (u)<-[:BOUGHT_BY]-(:Order)<-[:IN_ORDER]-(oit) )\
        WITH oit, COUNT(*) AS cs \
        SKIP %d LIMIT %d \
        OPTIONAL MATCH (:User)<-[rv:REVIEWED_BY]-(oit) \
        WITH oit, COUNT(rv) as crv, cs \
        RETURN oit, crv ORDER BY cs"
        % (userId, start, limit))
        return [(Item.inflate(row[0]), row[1]) for row in results]

    @classmethod
    def collaborative_order_normal(cls, userId, start=0, limit=24):
        results, meta = db.cypher_query("\
        MATCH (u:User {userId: \"%s\"})<-[:BOUGHT_BY]-(:Order)<-[:IN_ORDER]-(:Item)-[:IN_ORDER]->(:Order)-[:BOUGHT_BY]->(o:User) \
        MATCH (o)<-[:BOUGHT_BY]-(:Order)<-[:IN_ORDER]-(it:Item) \
        WHERE NOT EXISTS( (u)<-[:BOUGHT_BY]-(:Order)<-[:IN_ORDER]-(it) ) \
        WITH it, COUNT(o) AS co ORDER BY co DESC \
        OPTIONAL MATCH (:User)<-[rv:REVIEWED_BY]-(it) \
        RETURN it, COUNT(rv)\
        SKIP %d LIMIT %d" % (userId, start, limit))
        return [(Item.inflate(row[0]), row[1]) for row in results]

    @classmethod
    def collaborative_review_normal(cls, userId, start=0, limit=24):
        results, meta = db.cypher_query("\
        MATCH (u:User {userId: \"%s\"})<-[rv:REVIEWED_BY]-(:Item)-[:REVIEWED_BY]->(o:User) \
        WITH u, o, avg(rv.overall) AS mean \
        MATCH (o)<-[r:REVIEWED_BY]-(it:Item) \
        WHERE NOT EXISTS( (u)<-[:REVIEWED_BY]-(it) ) \
        AND NOT EXISTS( (u)<-[:BOUGHT_BY]-(:Order)<-[:IN_ORDER]-(it) ) \
        AND r.overall >= mean \
        WITH it, COUNT(o) AS co ORDER BY co DESC \
        OPTIONAL MATCH (:User)<-[rv:REVIEWED_BY]-(it) \
        RETURN it, COUNT(rv)\
        SKIP %d LIMIT %d" % (userId, start, limit))
        return [(Item.inflate(row[0]), row[1]) for row in results]

    @classmethod
    def collaborative_review_ml(cls, userId, start=0, limit=24):
        results, meta = db.cypher_query("\
        MATCH (me:User {userId: \"%s\"})<-[rvm:REVIEWED_BY]-(it:Item) \
        WITH me, gds.alpha.similarity.asVector(it, rvm.overall) AS meVector \
        MATCH (you:User)<-[rvy:REVIEWED_BY]-(it) WHERE you <> me \
        \
        WITH me, you, meVector, gds.alpha.similarity.asVector(it, rvy.overall) AS youVector \
        WHERE size(apoc.coll.intersection([v in meVector | v.category], [v in youVector | v.category])) > 9 \
        \
        WITH me, you, gds.alpha.similarity.pearson(meVector, youVector, {vectorType: \"maps\"}) AS similarity \
        ORDER BY similarity DESC LIMIT 10 \
        \
        MATCH (you)<-[r:REVIEWED_BY]-(it:Item) \
        WHERE NOT EXISTS( (me)<-[:REVIEWED_BY]-(it) ) \
        AND NOT EXISTS( (me)<-[:BOUGHT_BY]-(:Order)<-[:IN_ORDER]-(it) ) \
        WITH it, SUM( similarity * r.overall ) AS score \
        ORDER BY score DESC SKIP %d LIMIT %d \
        \
        MATCH (:User)<-[r:REVIEWED_BY]-(it) \
        RETURN it, COUNT(r), score" 
        % (userId, start, limit))
        return [(Item.inflate(row[0]), row[1], row[2]) for row in results]

class Cart(StructuredRel):
    price = FloatProperty(required=True)
    quantity = FloatProperty(required=True)
    subTotal = FloatProperty(required=True)

class OrderPartial(StructuredRel):
    price = FloatProperty(required=True)
    quantity = FloatProperty(required=True)
    subTotal = FloatProperty(required=True)

class OrderOwner(StructuredRel):
    pass

class Review(StructuredRel):
    overall = FloatProperty()
    reviewText = StringProperty(required=True)
    reviewTime = StringProperty(required=True)

class Category(StructuredNode):
    index = IntegerProperty(unique_index=True, required=True)
    category = StringProperty(required=True)

    # items = RelationshipTo(Item, "HAS")
    # parents = RelationshipTo(Category, "HAS_PARENT")
    # children = RelationshipFrom(Category, "HAS_PARENT")

class Item(StructuredNode):
    index = IntegerProperty(unique_index=True, required=True)
    itemId = StringProperty(unique_index=True, required=True)
    title = StringProperty(required=True)
    description = StringProperty()
    brand = StringProperty()
    imUrl = StringProperty(required=True)
    price = FloatProperty(required=True)
    reviewOverall = FloatProperty(required=True)

    # orders = RelationshipTo(Order, "IN_ORDER")
    categories = RelationshipFrom(Category, "HAS")
    # carted_users = RelationshipTo(User, "IN_CART")
    # reviewed_users = RelationshipTo(User, "REVIEWED_BY")

class Order(StructuredNode):
    index = IntegerProperty(unique_index=True, required=True)
    time = StringProperty(required=True)
    totalPrice = FloatProperty(required=True)

    # bought_users = RelationshipTo(User, "BOUGHT_BY")
    items = RelationshipFrom(Item, "IN_ORDER", model=OrderPartial)
    
class User(StructuredNode):
    index = IntegerProperty(unique_index=True, required=True)
    name = StringProperty(required=True)
    password = StringProperty(required=True)
    userId = StringProperty(unique_index=True, required=True)

    owned_orders = RelationshipFrom(Order, "BOUGHT_BY", model=OrderOwner)
    cart_items = RelationshipFrom(Item, "IN_CART", model=Cart)
    review_items = RelationshipFrom(Item, "REVIEWED_BY", model=Review)
