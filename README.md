# E-commerce website using Neo4J GraphDB

## How to deploy

1. Consider Neo4J database running
2. Edit [.env](.env) and [app/.env](app/.env) for Neo4J address and authencation information
3. Intall requires packages
'''
pip install -r requirements.txt
'''
4. Start web server
'''
gunicorn app:app
'''
5. Open your brower and enjoy ^_^

**Note:**  *If you have docker installed, you can replace step 3 and step 4 by simply run*
'''
docker-compose up -d
'''
