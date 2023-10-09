import threading
from typing import List

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class DBEngine(object):
    def __init__(self,
                 user: str,
                 password: str,
                 db_name: str,
                 host: str,
                 echo: bool = False):
        self.user = user
        self.password = password
        self.db_name = db_name
        self.host = host
        self.echo = echo
        self.engine = None
        self.Session = None
        self.locker = threading.Lock()

    def connect(self):
        self.engine = create_engine(
            f"mysql+pymysql://{self.user}:{self.password}@{self.host}/{self.db_name}?charset=utf8", echo=self.echo)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def new_session(self):
        if self.Session is None:
            raise Exception("DB connection not established")
        return self.Session()


dbEngine = DBEngine(user=u"dashuai", password=u" ", db_name=u"test", host=u"10.5.10.97")


def paged_find_and_count(query_model,
                         cond,
                         orders: List,
                         page_size: int = 10,
                         page_number: int = 1):
    with dbEngine.locker:
        session = dbEngine.new_session()
        offset_count = page_size * (page_number - 1)
        if (not isinstance(orders, list)) or len(orders) == 0:
            orders = [None]
        try:
            if cond is not None:
                non_paged_results = session.query(query_model).filter(cond)
                if page_size > 0:
                    paged_results = session.query(query_model).filter(cond).order_by(*orders).offset(
                        offset_count).limit(page_size)
                    return non_paged_results.count(), paged_results.all()
                else:
                    paged_results = session.query(query_model).filter(cond).order_by(*orders)
                    return non_paged_results.count(), paged_results.all()

            else:
                non_paged_results = session.query(query_model)
                if page_size > 0:
                    paged_results = session.query(query_model).order_by(*orders).offset(offset_count).limit(page_size)
                    return non_paged_results.count(), paged_results.all()
                else:
                    paged_results = session.query(query_model).order_by(*orders)
                    return non_paged_results.count(), paged_results.all()

        finally:
            session.close()
