#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database Operations
"""

from ig_s import en

import psycopg2
from datetime import datetime, timedelta

def db_connect(host, database, user, password):

    # TODO: retrieve credentials from file
    return psycopg2.connect(host=host, database=database, user=user, password=password)

def execute_query(query, values=None):
    conn = db_connect()
    cur = conn.cursor()

    if values is None:
        cur.execute(query)
    else:
        cur.execute(query, values)
    conn.commit()

    try:
        result = cur.fetchall()
    except:
        result = 'Query executed, no resuts to fetch'

    cur.close()
    conn.close()
    return result


