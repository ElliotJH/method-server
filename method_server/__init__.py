import argparse
import re
import os
from aiohttp import web

import method_server.models
from . import db, methods, json

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--create', action='store_true')
    args = parser.parse_args()
    database = db.Database(os.environ.get('DATABASE_URL'))
    method_db = methods.MethodDatabase(database)
    if args.create:
        method_db.update()


    async def do_search(request):
        q = request.query.get('query')
        if not isinstance(q, str):
            return web.HTTPBadRequest(reason="Include a string query", headers={'Access-Control-Allow-Origin': '*'})

        if len(q) < 3:
            return web.HTTPBadRequest(reason="Must have at least 3 characters in the search string", headers={'Access-Control-Allow-Origin': '*'})
        search_string = re.sub('[^a-z ]', '', q.lower()) # abundance of caution
        return web.json_response({'methods' : method_db.find_methods(search_string)},
                                 dumps=json.dumps,
                                 headers={'Access-Control-Allow-Origin': '*'})

    app = web.Application()
    app.router.add_get('/method', do_search)

    web.run_app(app, port=int(os.environ.get('PORT', 8081)))
