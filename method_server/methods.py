import zipfile
from contextlib import closing

from lxml import objectify
import requests
import io

from sqlalchemy.orm import raiseload, eagerload

from method_server import models


class InvalidMethodsFileError(ValueError):
    pass


class MethodDatabase:
    def __init__(self, database):
        self.database = database

    def update(self):
        """Load the methods database file into sql"""
        resp = requests.get("http://methods.org.uk/method-collections/xml-zip-files/allmeths-xml.zip")
        with io.BytesIO(resp.content) as downloaded:
            with zipfile.ZipFile(downloaded) as zf:
                if len(zf.filelist) != 1:
                    raise InvalidMethodsFileError(f"Zip should contain precisely one file.")

                with zf.open(zf.filelist[0].filename) as f:
                    tree = objectify.parse(f)

        collection = tree.getroot()
        # collection
        # - collectionname
        # - notes
        # * methodSet
        #   - notes
        #   - properties
        #   * method
        with closing(self.database.session()) as session:
            for method_set_id, method_set in enumerate(collection.methodSet):
                stage = method_set.properties.stage.pyval
                name = method_set.notes.text
                method_set_m = models.MethodSet(stage=int(stage), name=name, id=method_set_id)
                methods = []
                for method_id_in_set, method in enumerate(method_set.method, 1):
                    method_id = method_set_id * 100000 + method_id_in_set
                    method_name = method.title.text
                    notation = method.notation.text
                    method_model = models.Method(id=method_id, name=method_name, notation=notation, method_set=method_set_m)
                    methods.append(method_model)
                session.add_all([method_set_m, *methods])
            session.commit()

    def find_methods(self, search_string, stage=None, limit=100):
        """Find all methods that match the search string"""
        with closing(self.database.session()) as session:
            wildcard_search_string = search_string.replace(' ', '%')
            q = session.query(models.Method).filter(models.Method.name.ilike(f'%{wildcard_search_string}%'))
            if stage:
                q = q.filter(models.Method.stage == stage)
            if limit:
                q = q.limit(limit)

            return q.options(eagerload('*')).all()

    def lookup_pn(self, method):
        if not method.definitions:
            self.api.get_lead_head_and_blocks(method.method_db_id)

    def count_methods(self):
        with closing(self.database.session()) as session:
            return session.query(models.Method).count()

class ArgumentError(ValueError): pass
