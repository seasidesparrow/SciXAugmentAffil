import html
from affildb import normalize
from affildb import db as affdb
from SciXPipelineUtils import utils
from SciXPipelineUtils.scix_uuid import scix_uuid as uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


# define the Augment_Affil class, then create task that calls it.

class Augment_Affil(object):
    def __init__(self):
        pass

    def _build_aff_id(self):
        aff_id = []
        for auth in self.author_data:
            author_affid_string = "; ".join([a.get("inst_id", "-") for a in auth])
            aff_id.append(author_affid_string)
        self.aff_id = aff_id

    def _build_aff_canonical(self):
        aff_canonical = []
        for auth in self.author_data:
            author_canonical_string = "; ".join([a.get("inst_canonical", "-") for a in auth])
            aff_canonical.append(author_canonical_string)
        self.aff_canonical = aff_canonical

    def _build_aff_country(self):
        aff_country = []
        for auth in self.author_data:
            author_country_string = "; ".join([a.get("inst_country", "-") for a in auth])
            aff_country.append(author_country_string)
        self.aff_country = aff_country

    def _build_aff_iso_country(self):
        aff_iso_country = []
        for auth in self.author_data:
            author_iso_country_string = "; ".join([a.get("inst_iso_country", "-") for a in auth])
            aff_iso_country.append(author_iso_country_string)
        self.aff_iso_country = aff_iso_country

    def _build_parents(self):
        self.aff_facet_hier = []
        self.aff_abbrev = []
        for auth in self.author_data:
            auth_aff_abbrev = []
            for aff in auth:
                aff_abbrev = aff.get("inst_abbreviation", "-")
                if aff_abbrev == "-":
                    auth_aff_abbrev.append(aff_abbrev)
                else:
                    aff_parents = aff.get("parent_data", [])
                    parent_abbrev = [p.get("inst_abbreviation", "-") for p in aff_parents]
                    if parent_abbrev:
                        pc_list = ["%s/%s" % (p, aff_abbrev) for p in parent_abbrev]
                        abbrev_string = "; ".join(pc_list)
                        for p in parent_abbrev:
                            facet_0 = "0/%s" % p
                            facet_1 = "1/%s/%s" % (p, aff_abbrev)
                            if facet_0 not in self.aff_facet_hier:
                                self.aff_facet_hier.append(facet_0)
                            if facet_1 not in self.aff_facet_hier:
                                self.aff_facet_hier.append(facet_1)
                    else:
                        abbrev_string = "%s/%s" % (aff_abbrev, aff_abbrev)
                        facet_0 = "0/%s" % aff_abbrev
                        facet_1 = "1/%s/%s" % (aff_abbrev, aff_abbrev)
                        if facet_0 not in self.aff_facet_hier:
                            self.aff_facet_hier.append(facet_0)
                        if facet_1 not in self.aff_facet_hier:
                            self.aff_facet_hier.append(facet_1)
                    auth_aff_abbrev.append(abbrev_string)
            self.aff_abbrev.append("; ".join(auth_aff_abbrev))

    def _build_output(self):
        self.aff = self.record.get("aff", [])
        self._build_aff_canonical()
        self._build_aff_country()
        self._build_aff_iso_country()
        self._build_aff_id()
        self._build_parents()
        self.author = self.record.get("author", [])
        self.bibcode = self.record.get("bibcode", "")
        self.scixID = self.record.get("scixID", "")
        self.output = {
            "aff": self.aff,
            "aff_abbrev": self.aff_abbrev,
            "aff_country": self.aff_country,
            "aff_canonical": self.aff_canonical,
            "aff_facet_hier": self.aff_facet_hier,
            "aff_id": self.aff_id,
            "aff_iso_country": self.aff_iso_country,
            "author": self.author,
            "bibcode": self.bibcode,
            "scix_id": self.scixID,
        }

    def parse(self, record, author_data):
        self.record = record
        self.author_data = author_data
        self._build_output()
        return self.output


def augment_storage_record(app, record, norm):
    # Receives msgs with master_pipeline.records.bib_data format
    # Sends msgs with master_pipeline.records.augments format
    try:
        
        author_data = []
        affils = record.get("aff", [])
        found = {}
        for auth in affils:
            auth = html.unescape(auth)
            alist = auth.split(";")
            author_aff = []
            for a in alist:
                if norm:
                    query_string = normalize.normalize_string(a,
                        kill_spaces = app.conf.get("NORM_KILL_SPACES", False),
                        upper_case = app.conf.get("NORM_UPPER_CASE", False)
                    )
                else:
                    query_string = normalize.clean_string(a)
                # if you've already found this string, don't bother
                # querying the database again
                if found.get(query_string, None):
                    res = found.get(query_string)
                else:
                    res = affdb.query_one_string(app, query_string, norm)
                    found[query_string] = res
                author_aff.append(res)
            author_data.append(author_aff)
        augment_affil = aa().parse(record, author_data)
        augment_affil["record_id"] = uuid.uuid7()
        return augment_affil
    except Exception as err:
        logger.error("Record affil augment failed: %s" % err)


