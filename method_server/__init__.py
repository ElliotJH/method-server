import argparse
import logging
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
            logging.error("do_search: bad request, no string query included")
            return web.HTTPBadRequest(reason="Include a string query", headers={'Access-Control-Allow-Origin': '*'})

        if len(q) < 3:
            logging.info("do_search: bad request, query is too show")
            return web.HTTPBadRequest(reason="Must have at least 3 characters in the search string", headers={'Access-Control-Allow-Origin': '*'})
        search_string = re.sub('[^a-z ]', '', q.lower()) # abundance of caution
        search_result = method_db.find_methods(search_string)
        logging.info(f"do_search: searching for {search_string}, {len(search_result)} results")
        return web.json_response({'methods' : search_result},
                                 dumps=json.dumps,
                                 headers={'Access-Control-Allow-Origin': '*'})

    async def get_status(request):
        return web.json_response({
            'status' : 'OK',
            'methods' : {
                'count' : method_db.count_methods()
            }
        })

    app = web.Application()
    app.router.add_get('/method', do_search)
    app.router.add_get('/healthz', get_status)

    web.run_app(app, port=int(os.environ.get('PORT', 8081)))
